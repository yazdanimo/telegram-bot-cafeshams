# fetch_news.py
import aiohttp, asyncio, json, time, hashlib, feedparser, re
from urllib.parse import urlparse, urlunparse, parse_qsl
from bs4 import BeautifulSoup
from translatepy import Translator

from utils import load_sources, extract_full_content, summarize_text, format_news
from handlers import send_news_with_button

SEND_INTERVAL      = 3
LAST_SEND          = 0
SENT_URLS_FILE     = "sent_urls.json"
SENT_HASHES_FILE   = "sent_hashes.json"
BAD_LINKS_FILE     = "bad_links.json"
SKIPPED_LOG_FILE   = "skipped_items.json"
GARBAGE_NEWS_FILE  = "garbage_news.json"

translator = Translator()

def load_set(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_set(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

def normalize_url(url: str) -> str:
    p = urlparse(url)
    qs = [(k,v) for k,v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunparse((p.scheme,p.netloc,p.path,"","&".join(f"{k}={v}" for k,v in qs),""))

def is_garbage(text: str) -> bool:
    t = text.strip()
    if len(t) < 60: return True
    persian = re.findall(r"[\u0600-\u06FF]", t)
    if len(persian)/max(len(t),1) < 0.4: return True
    if re.search(r"(.)\1{5,}", t): return True
    if re.search(r"(ha){3,}|ههه{3,}", t): return True
    if len(re.findall(r"[!?.،؛…]{2,}", t)) > 5: return True
    latin = re.findall(r"[A-Za-z]{5,}", t)
    if len(latin) > 5 and len(persian) < 50: return True
    for kw in ["ثبت نام","login","register","ورود","signup","رمز عبور"]:
        if kw in t.lower(): return True
    return False

def log_garbage(src, link, title, content):
    try: items = json.load(open(GARBAGE_NEWS_FILE, "r", encoding="utf-8"))
    except: items=[]
    items.append({"source":src,"link":link,"title":title,"content":content[:300]})
    json.dump(items, open(GARBAGE_NEWS_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def log_skipped(src,u,reason,title=None):
    try: items = json.load(open(SKIPPED_LOG_FILE, "r", encoding="utf-8"))
    except: items=[]
    items.append({"source":src,"url":u,"title":title,"reason":reason})
    json.dump(items, open(SKIPPED_LOG_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

async def safe_send(bot, chat_id, text, **k):
    global LAST_SEND
    d = time.time()-LAST_SEND
    if d < SEND_INTERVAL: await asyncio.sleep(SEND_INTERVAL-d)
    try: return await bot.send_message(chat_id=chat_id, text=text, **k)
    except Exception as e: print("⚠️ send:",e)
    finally: LAST_SEND = time.time()

async def parse_rss_async(url):
    try:
        dp = await asyncio.wait_for(asyncio.to_thread(feedparser.parse, url), timeout=10)
        return dp.entries or []
    except Exception as e:
        print(f"⚠️ RSS {url}:", e)
        return []

async def fetch_html(session, url):
    try:
        async with session.get(url) as r:
            if r.status!=200: raise Exception(f"HTTP {r.status}")
            return await r.text()
    except Exception as e:
        print(f"❌ HTML {url}:", e)
        return ""

async def process_content(full_text: str, lang: str) -> str:
    text = full_text
    if lang.lower()=="en":
        try:
            tr = await asyncio.to_thread(translator.translate, full_text, "fa")
            text = getattr(tr,"result",str(tr))
        except Exception as e:
            print("⚠️ translate:", e)
    return await asyncio.to_thread(summarize_text, text)

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad = load_set(BAD_LINKS_FILE)
    stats, sent_now, hashes_now = [], set(), set()

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        for src in load_sources():
            name, rss, fb, lang = src["name"], src["rss"], src["fallback"], src.get("lang","fa")
            sent = err = 0
            items = await parse_rss_async(rss)
            total = len(items)
            print(f"📥 دریافت {total} آیتم از {name}")

            for it in items[:3]:
                raw = it.get("link",""); u = normalize_url(raw)
                if not u or u in sent_urls or u in sent_now or u in bad:
                    log_skipped(name,u,"تکراری",it.get("title")); continue
                try:
                    html = await fetch_html(session, raw)
                    full = extract_full_content(html)
                    summ = await process_content(full, lang)
                    if is_garbage(full) or is_garbage(summ):
                        log_skipped(name,u,"بی‌کیفیت",it.get("title"))
                        log_garbage(name,raw,it.get("title",""),full)
                        bad.add(u); err+=1; continue

                    cap = format_news(name,it.get("title",""),summ,raw)
                    h   = hashlib.md5(cap.encode("utf-8")).hexdigest()
                    if h in sent_hashes or h in hashes_now:
                        log_skipped(name,u,"تکراری",it.get("title")); continue

                    await send_news_with_button(bot, chat_id, cap)
                    sent_now.add(u); hashes_now.add(h); sent+=1

                except Exception as e:
                    log_skipped(name,u,f"خطا: {e}",it.get("title"))
                    print("⚠️ proc:",raw,"→",e)
                    bad.add(u); err+=1

            # fallback (همانند بالا)...

            stats.append({"source":name,"fetched":total,"sent":sent,"errors":err})

        sent_urls.update(sent_now); sent_hashes.update(hashes_now)
        save_set(sent_urls,SENT_URLS_FILE); save_set(sent_hashes,SENT_HASHES_FILE)
        save_set(bad,BAD_LINKS_FILE)

        # report
        hdr = ["Source","Fetched","Sent","Errors"]
        w = {h:len(h) for h in hdr}
        w["Source"] = max(w["Source"],max(len(r["source"]) for r in stats))
        for r in stats:
            w["Fetched"]=max(w["Fetched"],len(str(r["fetched"])))
            w["Sent"]=max(w["Sent"],len(str(r["sent"])))
            w["Errors"]=max(w["Errors"],len(str(r["errors"])))
        lines = ["📊 News Aggregation Report:\n",
                 "  ".join(f"{h:<{w[h]}}" for h in hdr),
                 "  ".join("-"*w[h] for h in hdr)]
        for r in stats:
            lines.append("  ".join([
                f"{r['source']:<{w['Source']}}",
                f"{r['fetched']:>{w['Fetched']}}",
                f"{r['sent']:>{w['Sent']}}",
                f"{r['errors']:>{w['Errors']}}"
            ]))
        report = "<pre>"+ "\n".join(lines)+"</pre>"
        await safe_send(bot, chat_id, report, parse_mode="HTML")
