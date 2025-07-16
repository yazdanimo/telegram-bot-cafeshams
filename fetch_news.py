import aiohttp
import asyncio
import time
import hashlib
import logging
import feedparser
import re
from urllib.parse import urlparse, urlunparse, parse_qsl
from bs4 import BeautifulSoup
from translatepy import Translator
from utils import (
    load_sources,
    extract_full_content,
    summarize_fa,
    summarize_en,
    format_news,
    load_set,
    save_set,
    is_garbage,
    safe_send
)
from handlers import send_news_with_button

SEND_INTERVAL  = 15
MAX_PER_SOURCE = 3
FILES = {
    "urls":   "sent_urls.json",
    "hashes": "sent_hashes.json",
    "bad":    "bad_links.json"
}

translator = Translator()

def normalize_url(url: str) -> str:
    p  = urlparse(url)
    qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunparse((p.scheme, p.netloc, p.path, "", "&".join(f"{k}={v}" for k, v in qs), ""))

async def parse_rss(url: str):
    dp = await asyncio.to_thread(feedparser.parse, url)
    return dp.entries or []

async def fetch_html(session, url: str) -> tuple[str, str]:
    try:
        async with session.get(url, timeout=15) as r:
            if r.status == 200:
                return await r.text(), str(r.url)
    except:
        pass
    return "", url

async def fetch_and_send_news(bot, chat_id, sent_urls: set, sent_hashes: set):
    bad      = load_set(FILES["bad"])
    stats    = []
    new_urls = set()
    new_h    = set()

    async with aiohttp.ClientSession() as sess:
        for src in load_sources():
            name, rss, fb, lang = src["name"], src["rss"], src["fallback"], src["lang"]
            got = sent = err = 0

            logging.info(f"📡 fetching {name}")
            items = await parse_rss(rss)
            got = len(items)
            for entry in items[:MAX_PER_SOURCE]:
                link = entry.get("link", "").strip()
                u    = normalize_url(link)
                if not u or u in sent_urls|new_urls|bad:
                    continue

                html, final_url = await fetch_html(sess, link)
                full = extract_full_content(html)
                if is_garbage(full):
                    bad.add(u); err += 1; continue

                if lang == "en":
                    try:
                        tr = await asyncio.to_thread(translator.translate, full, "fa")
                        fa_text = getattr(tr, "result", str(tr))
                        summ = summarize_fa(fa_text)
                    except Exception as e:
                        logging.warning(f"⚠️ Translation failed: {e}")
                        summ = summarize_fa(full)
                else:
                    summ = summarize_fa(full)

                if is_garbage(summ):
                    bad.add(u); err += 1; continue

                title = entry.get("title", "").strip() or name
                text  = format_news(name, title, summ, final_url)
                h     = hashlib.md5(text.encode()).hexdigest()
                if h in sent_hashes|new_h:
                    continue

                logging.info(f"✅ Sending: {title}")
                await send_news_with_button(bot, chat_id, text)
                await asyncio.sleep(1.5)  # جلوگیری از Flood control
                new_urls.add(u); new_h.add(h); sent += 1

            stats.append({"src":name,"got":got,"sent":sent,"err":err})

    sent_urls   |= new_urls
    sent_hashes |= new_h
    save_set(sent_urls,   FILES["urls"])
    save_set(sent_hashes, FILES["hashes"])
    save_set(bad,         FILES["bad"])

    hdr = ["Source","Got","Sent","Err"]
    w   = {h:len(h) for h in hdr}
    for r in stats:
        w["Source"] = max(w["Source"], len(r["src"]))
        w["Got"]    = max(w["Got"],    len(str(r["got"])))
        w["Sent"]   = max(w["Sent"],   len(str(r["sent"])))
        w["Err"]    = max(w["Err"],    len(str(r["err"])))

    lines=["📊 News Report:\n",
           "  ".join(f"{h:<{w[h]}}" for h in hdr),
           "  ".join("-"*w[h] for h in hdr)]
    for r in stats:
        lines.append("  ".join([
            f"{r['src']:<{w['Source']}}",
            f"{r['got']:>{w['Got']}}",
            f"{r['sent']:>{w['Sent']}}",
            f"{r['err']:>{w['Err']}}"
        ]))

    report="<pre>"+ "\n".join(lines) +"</pre>"
    logging.info("📑 sending report")
    await safe_send(bot, chat_id, report, parse_mode="HTML")
