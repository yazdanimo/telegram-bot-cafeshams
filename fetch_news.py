import aiohttp
import asyncio
import json
import time
import hashlib
import feedparser
import re

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qsl
from translatepy import Translator

from utils import load_sources, extract_full_content, summarize_text, format_news
from handlers import send_news_with_button

# تنظیمات فایل‌ها و زمان‌بندی
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
    qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    query = "&".join(f"{k}={v}" for k, v in qs)
    return urlunparse((p.scheme, p.netloc, p.path, "", query, ""))

def is_garbage(text: str) -> bool:
    t = text.strip()
    if len(t) < 60: return True
    persian = re.findall(r'[\u0600-\u06FF]', t)
    if len(persian)/max(len(t),1) < 0.4: return True
    if re.search(r'(.)\1{5,}', t): return True
    if re.search(r'(ha){3,}|ههه{3,}', t): return True
    if len(re.findall(r'[!?.،؛…]{2,}', t)) > 5: return True
    latin = re.findall(r'[A-Za-z]{5,}', t)
    if len(latin) > 5 and len(persian) < 50: return True
    for kw in ["ثبت نام","login","register","ورود","signup","رمز عبور"]:
        if kw in t.lower(): return True
    return False

def log_garbage(src, link, title, content):
    try: items = json.load(open(GARBAGE_NEWS_FILE,"r",encoding="utf-8"))
    except: items = []
    items.append({"source":src,"link":link,"title":title,"content":content[:300]})
    json.dump(items, open(GARBAGE_NEWS_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def log_skipped(src, u, reason, title=None):
    try: items = json.load(open(SKIPPED_LOG_FILE,"r",encoding="utf-8"))
    except: items = []
    items.append({"source":src,"url":u,"title":title,"reason":reason})
    json.dump(items, open(SKIPPED_LOG_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

async def safe_send(bot, chat_id, text, **kwargs):
    global LAST_SEND
    elapsed = time.time() - LAST_SEND
    if elapsed < SEND_INTERVAL:
        await asyncio.sleep(SEND_INTERVAL - elapsed)
    try:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        print("⚠️ send error:", e)
    finally:
        LAST_SEND = time.time()

async def parse_rss_async(url):
    try:
        dp = await asyncio.wait_for(asyncio.to_thread(feedparser.parse, url), timeout=10)
        return dp.entries or []
    except Exception as e:
        print(f"⚠️ RSS error {url}:", e)
        return []

async def fetch_html(session, url):
    try:
        async with session.get(url) as res:
            if res.status != 200:
                raise Exception(f"HTTP {res.status}")
            return await res.text()
    except Exception as e:
        print(f"❌ HTML error {url}:", e)
        return ""

async def process_content(full_text: str, lang: str) -> str:
    text_for_summary = full_text
    if lang.lower() == "en":
        try:
            tr = await asyncio.to_thread(translator.translate, full_text, "fa")
            text_for_summary = getattr(tr, "result", str(tr))
        except Exception as e:
            print("⚠️ translate error:", e)
    return await asyncio.to_thread(summarize_text, text_for_summary)

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad_links   = load_set(BAD_LINKS_FILE)
    stats       = []
    sent_now    = set()
    hashes_now  = set()

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        for src in load_sources():
            name, rss, fb, lang = src["name"], src["rss"], src["fallback"], src.get("lang","fa")
            sent = err = 0
            items = await parse_rss_async(rss)
            total = len(items)
            print(f"📥 fetched {total} items from {name}")

            for item in items[:3]:
                raw = item.get("link",""); u = normalize_url(raw)
                if not u or u in sent_urls or u in sent_now or u in bad_links:
                    log_skipped(name, u, "duplicate", item.get("title"))
                    continue
                try:
                    html = await fetch_html(session, raw)
                    full = extract_full_content(html)
                    summ = await process_content(full, lang)

                    if is_garbage(full) or is_garbage(summ):
                        log_skipped(name, u, "low_quality", item.get("title"))
                        log_garbage(name, raw, item.get("title",""), full)
                        bad_links.add(u)
                        err += 1
                        continue

                    caption = format_news(name, item.get("title",""), summ, raw)
                    h = hashlib.md5(caption.encode("utf-8")).hexdigest()
                    if h in sent_hashes or h in hashes_now:
                        log_skipped(name, u, "duplicate", item.get("title"))
                        continue

                    await send_news_with_button(bot, chat_id, caption)
                    sent_now.add(u); hashes_now.add(h); sent += 1

                except Exception as e:
                    log_skipped(name, u, f"error: {e}", item.get("title"))
                    print("⚠️ process error", raw, "→", e)
                    bad_links.add(u); err += 1

            # fallback if no RSS items
            if total == 0 and fb:
                try:
                    idx = await fetch_html(session, fb)
                    soup = BeautifulSoup(idx, "html.parser")
                    base = urlparse(fb)
                    links = []
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("/"):
                            href = urlunparse((base.scheme, base.netloc, href,"","",""))
                        if urlparse(href).netloc == base.netloc and href not in links:
                            links.append(href)
                        if len(links) >= 3:
                            break

                    for link in links:
                        u = normalize_url(link)
                        if not u or u in sent_urls or u in sent_now or u in bad_links:
                            log_skipped(name, u, "fallback_duplicate", None)
                            continue
                        try:
                            html = await fetch_html(session, link)
                            full = extract_full_content(html)
                            summ = await process_content(full, lang)
                            if is_garbage(full) or is_garbage(summ):
                                log_skipped(name, u, "fallback_low_quality", None)
                                log_garbage(name, link, "fallback", full)
                                bad_links.add(u); err += 1; continue

                            caption = format_news(f"{name} - fallback", "fallback", summ, link)
                            h = hashlib.md5(caption.encode("utf-8")).hexdigest()
                            if h in sent_hashes or h in hashes_now:
                                log_skipped(name, u, "fallback_duplicate", None)
                                continue

                            await send_news_with_button(bot, chat_id, caption)
                            hashes_now.add(h); sent += 1

                        except Exception as fe:
                            log_skipped(name, link, f"fallback_error: {fe}", None)
                            print("❌ fallback error", name, "→", fe)
                            bad_links.add(u); err += 1

                except Exception as e:
                    log_skipped(name, fb, f"fallback_index_error: {e}", None)
                    print("⚠️ fallback index error:", e)
                    bad_links.add(fb); err += 1

            stats.append({"source":name, "fetched":total, "sent":sent, "errors":err})

        # save state
        sent_urls.update(sent_now); sent_hashes.update(hashes_now)
        save_set(sent_urls,   SENT_URLS_FILE)
        save_set(sent_hashes, SENT_HASHES_FILE)
        save_set(bad_links,   BAD_LINKS_FILE)

        # generate and send report
        headers = ["Source","Fetched","Sent","Errors"]
        widths  = {h:len(h) for h in headers}
        widths["Source"] = max(widths["Source"], max(len(r["source"]) for r in stats))
        for r in stats:
            widths["Fetched"] = max(widths["Fetched"], len(str(r["fetched"])))
            widths["Sent"]    = max(widths["Sent"],    len(str(r["sent"])))
            widths["Errors"]  = max(widths["Errors"],  len(str(r["errors"])))

        lines = [
            "📊 News Aggregation Report:\n",
            "  ".join(f"{h:<{widths[h]}}" for h in headers),
            "  ".join("-"*widths[h] for h in headers)
        ]
        for r in stats:
            lines.append("  ".join([
                f"{r['source']:<{widths['Source']}}",
                f"{r['fetched']:>{widths['Fetched']}}",
                f"{r['sent']:>{widths['Sent']}}",
                f"{r['errors']:>{widths['Errors']}}"
            ]))

        report = "<pre>" + "\n".join(lines) + "</pre>"
        await safe_send(bot, chat_id, report, parse_mode="HTML")
