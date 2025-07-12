# File: fetch_news.py

import aiohttp
import asyncio
import json
import time
import hashlib
import feedparser

from urllib.parse import urlparse, urlunparse, parse_qsl
from utils import load_sources, extract_full_content, summarize_text, format_news

BAD_LINKS_FILE = "bad_links.json"
SEND_INTERVAL  = 3
LAST_SEND      = 0

def load_set(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_set(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

def normalize_url(url):
    p  = urlparse(url)
    qs = [(k,v) for k,v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunparse((p.scheme, p.netloc, p.path, "", "&".join(f"{k}={v}" for k,v in qs), ""))

async def safe_send(bot, chat_id, text, **kwargs):
    global LAST_SEND
    now  = time.time()
    wait = SEND_INTERVAL - (now - LAST_SEND)
    if wait > 0:
        await asyncio.sleep(wait)
    try:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        print("⚠️ خطا در ارسال پیام →", e)
    finally:
        LAST_SEND = time.time()

async def parse_rss_async(url):
    """
    دریافت RSS با timeout و استفاده از feedparser
    تا ۱۰ ثانیه صبر می‌کند، بعد به‌صورت ایمن برمی‌گردد.
    """
    try:
        dp = await asyncio.wait_for(
            asyncio.to_thread(feedparser.parse, url),
            timeout=10
        )
        return dp.entries or []
    except asyncio.TimeoutError:
        print(f"⚠️ Timeout در خواندن RSS → {url}")
        return []
    except Exception as e:
        print(f"⚠️ خطا در parse RSS → {url} → {e}")
        return []

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad_links = load_set(BAD_LINKS_FILE)
    stats     = []

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        for src in load_sources():
            name, rss, fb = src.get("name"), src.get("rss"), src.get("fallback")
            sent, err, total = 0, 0, 0

            print("⏳ بررسی منبع:", name)
            # 1. خواندن RSS
            items = await parse_rss_async(rss)
            total = len(items)
            print(f"📥 دریافت {total} آیتم از {name}")

            if total == 0:
                print(f"⚠️ RSS خالی یا خطا برای {name}")
                err += 1
            else:
                # 2. ارسال حداکثر ۳ خبر
                for item in items[:3]:
                    raw = item.get("link") or ""
                    u   = normalize_url(raw)
                    if not u or u in sent_urls or u in bad_links:
                        continue

                    try:
                        # دریافت صفحه
                        async with session.get(raw) as res:
                            if res.status != 200:
                                raise Exception(f"HTTP {res.status}")
                            html = await res.text()

                        full = extract_full_content(html)
                        summ = summarize_text(full)
                        cap  = format_news(name, item.get("title",""), summ, raw)

                        # چک هش برای فیلتر محتوای تکراری
                        h = hashlib.md5(cap.encode("utf-8")).hexdigest()
                        if h in sent_hashes:
                            continue

                        await safe_send(bot, chat_id, cap, parse_mode="HTML")

                        # ذخیره بلافاصله
                        sent_urls.add(u)
                        save_set(sent_urls, "sent_urls.json")
                        sent_hashes.add(h)
                        save_set(sent_hashes, "sent_hashes.json")
                        sent += 1

                    except Exception as e:
                        print("⚠️ خطا در پردازش", raw, "→", e)
                        bad_links.add(u)
                        err += 1

            # 3. fallback در صورت خالی بودن RSS
            if total == 0 and fb:
                try:
                    print(f"⏳ اجرای fallback برای {name}")
                    async with session.get(fb) as res:
                        if res.status != 200:
                            raise Exception(f"HTTP {res.status}")
                        html = await res.text()
                    full = extract_full_content(html)
                    summ = summarize_text(full)
                    cap  = format_news(f"{name} - جایگزین", name, summ, fb)
                    await safe_send(bot, chat_id, cap, parse_mode="HTML")
                    sent += 1
                except Exception as fe:
                    print("❌ خطا در fallback", name, "→", fe)
                    bad_links.add(fb)
                    err += 1

            stats.append({"منبع": name, "دریافت": total, "ارسال": sent, "خطا": err})
            await safe_send(bot, chat_id, f"✅ {name} — دریافت:{total} ارسال:{sent} خطا:{err}")

        # ذخیره bad_links و ارسال جدول گزارش
        save_set(bad_links, BAD_LINKS_FILE)

        hdr = ["منبع","دریافت","ارسال","خطا"]
        w   = {h:len(h) for h in hdr}
        for r in stats:
            for h in hdr:
                w[h] = max(w[h], len(str(r[h])))

        lines = [
            "  ".join(f"{h:<{w[h]}}" for h in hdr),
            "  ".join("-"*w[h] for h in hdr)
        ]
        for r in stats:
            lines.append(
                "  ".join(
                    f"{r[h]:<{w[h]}}" if h=="منبع" else f"{r[h]:>{w[h]}}"
                    for h in hdr
                )
            )
        report = "<pre>" + "\n".join(lines) + "</pre>"
        await safe_send(bot, chat_id, report, parse_mode="HTML")
