import aiohttp
import asyncio
import time
import hashlib
import feedparser
import logging

from urllib.parse import urlparse, urlunparse, parse_qsl
from translatepy import Translator

from utils import (
    load_sources,
    extract_full_content,
    summarize_text_fa,
    summarize_text_en,
    format_news,
    load_set,
    save_set,
    is_garbage
)
from handlers import send_news_with_button

logging.basicConfig(level=logging.INFO)

SEND_INTERVAL    = 2
LAST_SEND        = 0
FILES = {
    "sent_urls":   "sent_urls.json",
    "sent_hashes": "sent_hashes.json",
    "bad_links":   "bad_links.json"
}

translator = Translator()

def normalize_url(url: str) -> str:
    p = urlparse(url)
    qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunparse((p.scheme, p.netloc, p.path, "", "&".join(f"{k}={v}" for k, v in qs), ""))

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
    return await asyncio.to_thread(lambda: feedparser.parse(url).entries)

async def fetch_html(session, url):
    try:
        async with session.get(url, timeout=15) as r:
            if r.status != 200:
                return ""
            return await r.text()
    except:
        return ""

async def process_summary(full: str, lang: str) -> str:
    if lang == "en":
        try:
            tr = await asyncio.to_thread(translator.translate, full, "fa")
            fa_text = getattr(tr, "result", str(tr))
            return summarize_text_fa(fa_text)
        except:
            return summarize_text_en(full)
    else:
        return summarize_text_fa(full)

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad = load_set(FILES["bad_links"])
    stats = []
    new_sent_urls, new_hashes = set(), set()

    async with aiohttp.ClientSession() as sess:
        for src in load_sources():
            name, rss, fb, lang = src["name"], src["rss"], src["fallback"], src["lang"]
            got = sent = err = 0

            logging.info(f"📡 fetching RSS for {name}")
            items = await parse_rss(rss)
            got = len(items)
            for entry in items[:5]:                # حداکثر ۵ خبر اول
                link = entry.get("link", "")
                u = normalize_url(link)
                if not u or u in sent_urls | new_sent_urls | bad:
                    continue

                html = await fetch_html(sess, link)
                full = extract_full_content(html)
                if is_garbage(full):
                    bad.add(u); err += 1; continue

                summary = await process_summary(full, lang)
                if is_garbage(summary):
                    bad.add(u); err += 1; continue

                title = entry.get("title", "").strip()
                text = format_news(name, title, summary, link)
                h = hashlib.md5(text.encode()).hexdigest()
                if h in sent_hashes | new_hashes:
                    continue

                logging.info(f"✅ Sending: {name} – {title}")
                await send_news_with_button(bot, chat_id, text)
                new_sent_urls.add(u); new_hashes.add(h); sent += 1

            stats.append({"src": name, "got": got, "sent": sent, "err": err})

    # ذخیره وضعیت
    sent_urls |= new_sent_urls
    sent_hashes |= new_hashes
    save_set(sent_urls,   FILES["sent_urls"])
    save_set(sent_hashes, FILES["sent_hashes"])
    save_set(bad,         FILES["bad_links"])

    # گزارش جدول
    hdr = ["Source", "Got", "Sent", "Err"]
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
    await safe_send(bot, chat_id, report, parse_mode="HTML")
