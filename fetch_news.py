# File: fetch_news.py

import aiohttp
import asyncio
import json
import time
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl

from utils import load_sources, parse_rss, extract_full_content, summarize_text, format_news

BAD_LINKS_FILE = "bad_links.json"
SEND_INTERVAL  = 3
LAST_SEND      = 0

def load_set(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_set(data, file):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

def normalize_url(url):
    p = urlparse(url)
    qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunparse((p.scheme, p.netloc, p.path, "", "&".join(f"{k}={v}" for k, v in qs), ""))

async def safe_send(bot, chat_id, text, **kwargs):
    global LAST_SEND
    now = time.time()
    wait = SEND_INTERVAL - (now - LAST_SEND)
    if wait > 0:
        await asyncio.sleep(wait)
    try:
        msg = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        print("⚠️ خطا در ارسال پیام →", e)
        return None
    LAST_SEND = time.time()
    return msg

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    sources   = load_sources()
    bad_links = load_set(BAD_LINKS_FILE)
    stats     = []

    for src in sources:
        name, rss, fb = src.get("name"), src.get("rss"), src.get("fallback")
        sent, err, total = 0, 0, 0

        print("⏳ شروع بررسی", name)
        try:
            items = parse_rss(rss) or []
            total = len(items)
            print("📥 دریافت", total, "آیتم از", name)
            if total == 0:
                raise Exception()

            for item in items[:3]:
                link = item.get("link")
                u = normalize_url(link)
                if not u or u in sent_urls or u in bad_links:
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=10) as res:
                            if res.status != 200:
                                bad_links.add(u)
                                err += 1
                                continue
                            html = await res.text()

                    full = extract_full_content(html)
                    summ = summarize_text(full)
                    cap  = format_news(name, item.get("title",""), summ, link)
                    h    = hashlib.md5(cap.encode("utf-8")).hexdigest()
                    if h in sent_hashes:
                        continue

                    await safe_send(bot, chat_id, cap, parse_mode="HTML")
                    sent_urls.add(u)
                    save_set(sent_urls, "sent_urls.json")
                    sent_hashes.add(h)
                    save_set(sent_hashes, "sent_hashes.json")
                    sent += 1
                    await asyncio.sleep(1)

                except Exception as e:
                    print("⚠️ خطا در پردازش", link, "→", e)
                    bad_links.add(u)
                    err += 1

        except:
            print("⚠️ خطا در دریافت از", name)
            err += 1
            if fb:
                path = urlparse(fb).path or "/"
                if path not in ("/","") and fb not in bad_links:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(fb, timeout=10) as res:
                                if res.status != 200:
                                    raise Exception()
                                html = await res.text()

                        full = extract_full_content(html)
                        summ = summarize_text(full)
                        cap  = format_news(f"{name} - گزارش جایگزین", name, summ, fb)
                        await safe_send(bot, chat_id, cap, parse_mode="HTML")
                        sent += 1
                        await asyncio.sleep(1)
                    except Exception as e:
                        print("❌ خطا در fallback", name, "→", e)
                        bad_links.add(fb)
                        err += 1

        stats.append({"منبع": name, "دریافت": total, "ارسال": sent, "خطا": err})
        if sent == 0:
            await safe_send(bot, chat_id, f"⚠️ از منبع {name} خبری ارسال نشد.")
        else:
            print("✅ پایان بررسی", name, "—", sent, "خبر ارسال شد")

    save_set(bad_links, BAD_LINKS_FILE)

    # جدول گزارش monospace
    hdr = ["منبع", "دریافت", "ارسال", "خطا"]
    w   = {h: len(h) for h in hdr}
    for r in stats:
        for h in hdr:
            w[h] = max(w[h], len(str(r[h])))

    lines = [
        "  ".join(f"{h:<{w[h]}}" for h in hdr),
        "  ".join("-" * w[h] for h in hdr)
    ]
    for r in stats:
        lines.append(
            "  ".join(
                f"{r[h]:<{w[h]}}" if h == "منبع" else f"{r[h]:>{w[h]}}"
                for h in hdr
            )
        )
    report = "<pre>" + "\n".join(lines) + "</pre>"
    await safe_send(bot, chat_id, report, parse_mode="HTML")
