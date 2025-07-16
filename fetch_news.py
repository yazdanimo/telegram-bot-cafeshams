import aiohttp
import asyncio
import time
import hashlib
import feedparser
import re
import json
import logging

from urllib.parse import urlparse, urlunparse, parse_qsl
from translatepy import Translator

from utils import (
    load_sources,
    extract_full_content,
    summarize_text,
    format_news,
    load_set,
    save_set
)
from handlers import send_news_with_button

logging.basicConfig(level=logging.INFO)

SEND_INTERVAL     = 3
LAST_SEND         = 0
SENT_URLS_FILE    = "sent_urls.json"
SENT_HASHES_FILE  = "sent_hashes.json"
BAD_LINKS_FILE    = "bad_links.json"
SKIPPED_LOG_FILE  = "skipped_items.json"
GARBAGE_NEWS_FILE = "garbage_news.json"

translator = Translator()

def normalize_url(url: str) -> str:
    p = urlparse(url)
    qs = [(k,v) for k,v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunparse((p.scheme,p.netloc,p.path,"","&".join(f"{k}={v}" for k,v in qs),""))

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

def log_json(path, item):
    try:
        arr = json.load(open(path, "r", encoding="utf-8"))
    except:
        arr = []
    arr.append(item)
    json.dump(arr, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

async def safe_send(bot, chat_id, text, **kwargs):
    global LAST_SEND
    diff = time.time() - LAST_SEND
    if diff < SEND_INTERVAL:
        await asyncio.sleep(SEND_INTERVAL - diff)
    try:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    finally:
        LAST_SEND = time.time()

async def parse_rss(url):
    try:
        dp = await asyncio.to_thread(feedparser.parse, url)
        return dp.entries or []
    except:
        return []

async def fetch_html(session, url):
    try:
        async with session.get(url) as r:
            if r.status != 200:
                raise Exception(f"HTTP {r.status}")
            return await r.text()
    except:
        return ""

async def process_content(full, lang):
    text = full
    if lang == "en":
        try:
            tr = await asyncio.to_thread(translator.translate, full, "fa")
            text = getattr(tr, "result", str(tr))
        except:
            pass
    return await asyncio.to_thread(summarize_text, text)

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad   = load_set(BAD_LINKS_FILE)
    stats = []
    sent_now, hashes_now = set(), set()

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(20)) as sess:
        for src in load_sources():
            name, rss, fb, lang = src["name"], src["rss"], src["fallback"], src["lang"]
            sent = err = 0

            logging.info(f"📡 fetching RSS for {name}")
            items = await parse_rss(rss)
            logging.info(f"📥 got {len(items)} items from {name}")

            for it in items[:3]:
                link = it.get("link", "")
                u = normalize_url(link)

                if not u:
                    logging.info(f"🚫 skip no-link: {name}")
                    continue

                if u in sent_urls | sent_now | bad:
                    logging.info(f"🚫 skip duplicate: {name} – {u}")
                    log_json(SKIPPED_LOG_FILE, {"src":name,"url":u,"reason":"dup"})
                    continue

                html = await fetch_html(sess, link)
                full = extract_full_content(html)
                summ = await process_content(full, lang)
                logging.debug(f"✂️ summary len={len(summ)}")

                if is_garbage(full) or is_garbage(summ):
                    logging.info(f"🚫 skip garbage: {name} – {u}")
                    log_json(SKIPPED_LOG_FILE, {"src":name,"url":u,"reason":"low"})
                    log_json(GARBAGE_NEWS_FILE, {"src":name,"url":link})
                    bad.add(u); err += 1
                    continue

                cap = format_news(name, it.get("title",""), summ, link)
                h = hashlib.md5(cap.encode()).hexdigest()
                if h in sent_hashes | hashes_now:
                    logging.info(f"🚫 skip duplicate hash: {name} – {u}")
                    continue

                logging.info(f"✅ Sending news: {name} – {u}")
                await send_news_with_button(bot, chat_id, cap)
                sent_now.add(u); hashes_now.add(h); sent += 1

            stats.append({"src":name,"got":len(items),"sent":sent,"err":err})

    sent_urls |= sent_now; sent_hashes |= hashes_now
    save_set(sent_urls,   SENT_URLS_FILE)
    save_set(sent_hashes, SENT_HASHES_FILE)
    save_set(bad,         BAD_LINKS_FILE)

    # ساخت و ارسال گزارش
    hdr = ["Source","Got","Sent","Err"]
    w = {h: len(h) for h in hdr}
    for r in stats:
        w["Source"] = max(w["Source"], len(r["src"]))
        w["Got"]    = max(w["Got"],    len(str(r["got"])))
        w["Sent"]   = max(w["Sent"],   len(str(r["sent"])))
        w["Err"]    = max(w["Err"],    len(str(r["err"])))

    lines = ["📊 News Report:\n",
             "  ".join(f"{h:<{w[h]}}" for h in hdr),
             "  ".join("-"*w[h] for h in hdr)]
    for r in stats:
        lines.append("  ".join([
            f"{r['src']:<{w['Source']}}",
            f"{r['got']:>{w['Got']}}",
            f"{r['sent']:>{w['Sent']}}",
            f"{r['err']:>{w['Err']}}"
        ]))

    report = "<pre>" + "\n".join(lines) + "</pre>"
    logging.info("📑 Sending report")
    await safe_send(bot, chat_id, report, parse_mode="HTML")
