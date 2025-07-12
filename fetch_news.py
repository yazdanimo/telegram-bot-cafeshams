# File: fetch_news.py

import aiohttp
import asyncio
import json
import time
from urllib.parse import urlparse

from utils import (
    load_sources,
    parse_rss,
    extract_full_content,
    summarize_text,
    format_news
)

BAD_LINKS_FILE = "bad_links.json"
SEND_INTERVAL = 3  # حداقل فاصله بین ارسال پیام‌ها (ثانیه)
_last_send = 0

def load_bad_links():
    try:
        with open(BAD_LINKS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_bad_links(bad_links):
    with open(BAD_LINKS_FILE, "w") as f:
        json.dump(list(bad_links), f)

async def safe_send(bot, chat_id, text, **kwargs):
    """
    ارسال پیام با رعایت محدودیت Flood Control تلگرام
    """
    global _last_send
    now = time.time()
    wait = SEND_INTERVAL - (now - _last_send)
    if wait > 0:
        await asyncio.sleep(wait)
    msg = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    _last_send = time.time()
    return msg

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources   = load_sources()
    bad_links = load_bad_links()

    for src in sources:
        name     = src.get("name", "بدون‌نام")
        rss_url  = src.get("rss")
        fallback = src.get("fallback")
        sent_cnt = 0

        print(f"⏳ شروع بررسی {name}")

        try:
            items = parse_rss(rss_url)
            print(f"📥 دریافت {len(items)} آیتم از {name}")
            if not items:
                raise Exception("هیچ خبری از RSS دریافت نشد")

            for item in items[:3]:
                link = item.get("link")
                if not link or link in sent_urls or link in bad_links:
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=10) as res:
                            if res.status != 200:
                                bad_links.add(link)
                                continue
                            html = await res.text()

                    full    = extract_full_content(html)
                    summ    = summarize_text(full)
                    title   = item.get("title", "").strip()
                    caption = format_news(name, title, summ, link)

                    await safe_send(
                        bot, chat_id,
                        text=caption[:4096],
                        parse_mode="HTML"
                    )

                    sent_urls.add(link)
                    sent_cnt += 1
                    await asyncio.sleep(1)  # مابین لینک‌ها یک ثانیه فاصله

                except Exception as e:
                    print(f"⚠️ خطا در پردازش {link} → {e}")
                    bad_links.add(link)

        except Exception as e:
            print(f"⚠️ خطا در دریافت از {name} → {e}")

            # fallback فقط برای URL مقاله (پوشه path خالی نباشد)
            if fallback:
                path = urlparse(fallback).path or "/"
                if path not in ("/", "") and fallback not in bad_links:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(fallback, timeout=10) as res:
                                if res.status != 200:
                                    raise Exception(f"HTTP {res.status}")
                                html = await res.text()

                        full    = extract_full_content(html)
                        summ    = summarize_text(full)
                        caption = format_news(
                            f"{name} - گزارش جایگزین",
                            name,
                            summ,
                            fallback
                        )

                        await safe_send(
                            bot, chat_id,
                            text=caption[:4096],
                            parse_mode="HTML"
                        )

                        sent_cnt += 1
                        await asyncio.sleep(1)

                    except Exception as fe:
                        print(f"❌ خطا در fallback {name} → {fe}")
                        bad_links.add(fallback)

        # گزارش نهایی هر منبع
        if sent_cnt == 0:
            await safe_send(
                bot, chat_id,
                text=f"⚠️ از منبع {name} هیچ خبری ارسال نشد."
            )
        else:
            print(f"✅ پایان بررسی {name} — {sent_cnt} خبر ارسال شد")

    save_bad_links(bad_links)
