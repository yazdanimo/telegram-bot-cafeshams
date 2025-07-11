import aiohttp
import asyncio
import json
from utils import (
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

async def fetch_tasnim_news(bot, chat_id, sent_urls):
    rss_url = "https://www.tasnimnews.com/rss"
    fallback = "https://www.tasnimnews.com"
    name = "Tasnim News"

    bad_links = load_bad_links()

    print(f"⏳ شروع بررسی {name}")

    try:
        items = parse_rss(rss_url)
        print(f"📥 دریافت {len(items)} آیتم از {name}")

        if not items:
            raise Exception("هیچ خبری دریافت نشد")

        for item in items[:2]:
            link = item.get("link")
            if not link or link in sent_urls or link in bad_links:
                print(f"🔁 لینک تکراری یا خراب: {link}")
                continue

            try:
                print(f"🔗 دریافت محتوای خبر: {link}")
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
                print(f"✅ ارسال موفق خبر: {link}")
                sent_urls.add(link)
                await asyncio.sleep(3)

            except Exception as e:
                print(f"⚠️ خطا در ارسال {link}: {e}")

    except Exception as rss_err:
        print(f"⚠️ خطا در RSS {name}: {rss_err}")

        if fallback not in sent_urls and fallback not in bad_links:
            try:
                print(f"🟡 اجرای fallback برای {name}")
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
                print(f"🟢 ارسال fallback موفق برای {name}")
                sent_urls.add(fallback)
                await asyncio.sleep(3)

            except Exception as f_err:
                print(f"❌ خطا در fallback {name}: {f_err}")
        else:
            print(f"🔁 fallback قبلاً ارسال شده یا خراب: {fallback}")

    save_bad_links(bad_links)
    print(f"✅ پایان بررسی {name}")
