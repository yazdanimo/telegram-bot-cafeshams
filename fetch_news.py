import aiohttp
import asyncio
import json
import os
from utils import (
    load_sources,
    extract_full_content,
    summarize_text,
    format_news,
    translate_text,
    is_persian,
    parse_rss
)

BAD_LINKS_FILE = "bad_links.json"

def load_bad_links():
    try:
        with open(BAD_LINKS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_bad_links(bad_links):
    with open(BAD_LINKS_FILE, "w") as f:
        json.dump(list(bad_links), f)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    bad_links = load_bad_links()
    fallback_sent = set()

    for src in sources:
        name = src.get("name", "بدون‌نام")
        rss_url = src.get("rss")
        fallback = src.get("fallback")
        category = src.get("category", "other")
        sent_count = 0

        print(f"⏳ شروع بررسی {name} [{category}]")

        try:
            items = parse_rss(rss_url)
            print(f"📥 دریافت {len(items)} آیتم از {name}")
            if not items:
                raise Exception("هیچ خبری دریافت نشد")

            for item in items[:3]:
                link = item.get("link")
                if not link or link in sent_urls or link in bad_links:
                    print(f"🔁 لینک تکراری یا خراب: {link}")
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=10) as res:
                            if res.status != 200:
                                print(f"❌ وضعیت HTTP: {res.status} → {link}")
                                bad_links.add(link)
                                continue
                            raw = await res.text()

                    title = item.get("title", "")
                    full_text = extract_full_content(raw)
                    summary = summarize_text(full_text)

                    if not is_persian(title + " " + summary):
                        title = translate_text(title)
                        summary = translate_text(summary)

                    caption = format_news(name, title, summary, link)
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")

                    sent_urls.add(link)
                    sent_count += 1
                    await asyncio.sleep(3)

                except Exception as e:
                    print(f"⚠️ خطا در پردازش {link}: {e}")
                    bad_links.add(link)

        except Exception as e:
            print(f"⚠️ خطا در دریافت از {name}: {e}")

            # Fallback
            if fallback and fallback not in sent_urls and fallback not in fallback_sent and fallback not in bad_links:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(fallback, timeout=10) as res:
                            if res.status != 200:
                                raise Exception(f"{res.status} → fallback")
                            raw = await res.text()

                    title = f"{name} - گزارش جایگزین"
                    full_text = extract_full_content(raw)
                    summary = summarize_text(full_text)

                    caption = format_news(name, title, summary, fallback)
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")

                    sent_urls.add(fallback)
                    fallback_sent.add(fallback)
                    print(f"🟢 ارسال fallback موفق برای {name}")
                    await asyncio.sleep(3)

                except Exception as f_err:
                    print(f"❌ خطا در fallback {name}: {f_err}")
                    bad_links.add(fallback)
            else:
                print(f"🔁 fallback قبلاً استفاده شده یا خراب: {fallback}")

        # گزارش ارسال‌ها
        if sent_count == 0:
            await bot.send_message(chat_id=chat_id, text=f"⚠️ از منبع {name} هیچ خبری ارسال نشد — احتمالاً لینک‌ها خراب یا فیلتر بودن.")
        else:
            print(f"✅ پایان بررسی {name} — {sent_count} خبر ارسال شد\n")

    save_bad_links(bad_links)
