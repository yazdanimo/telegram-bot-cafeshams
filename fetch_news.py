import aiohttp
import asyncio
from utils import (
    extract_full_content,
    summarize_text,
    format_news,
    translate_text,
    is_persian,
    parse_rss
)

async def fetch_tasnim_news(bot, chat_id, sent_urls):
    rss_url = "https://www.tasnimnews.com/rss"
    fallback = "https://www.tasnimnews.com"

    print("⏳ شروع بررسی Tasnim News")

    try:
        items = parse_rss(rss_url)
        print(f"📥 دریافت {len(items)} آیتم از Tasnim")

        if not items:
            raise Exception("هیچ خبری دریافت نشد")

        for item in items[:2]:
            link = item.get("link")
            if not link or link in sent_urls:
                print(f"🔁 لینک تکراری یا قبلاً ارسال شده: {link}")
                continue

            try:
                print(f"🔗 دریافت محتوای خبر: {link}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(link, timeout=10) as res:
                        if res.status != 200:
                            print(f"❌ لینک خراب ({res.status}): {link}")
                            continue
                        raw = await res.text()

                title = item.get("title", "")
                full_text = extract_full_content(raw)
                summary = summarize_text(full_text)

                if not is_persian(title + " " + summary):
                    title = translate_text(title)
                    summary = translate_text(summary)

                caption = format_news("Tasnim News", title, summary, link)
                await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                print(f"✅ خبر ارسال شد: {link}")
                sent_urls.add(link)
                await asyncio.sleep(3)

            except Exception as e:
                print(f"⚠️ خطا در پردازش خبر {link}: {e}")

    except Exception as rss_err:
        print(f"⚠️ خطا در RSS Tasnim → تلاش با fallback")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(fallback, timeout=10) as res:
                    if res.status != 200:
                        raise Exception(f"fallback خطا داد → {res.status}")
                    raw = await res.text()

            title = "گزارش جایگزین Tasnim"
            full_text = extract_full_content(raw)
            summary = summarize_text(full_text)
            caption = format_news("Tasnim News", title, summary, fallback)

            if fallback not in sent_urls:
                await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                sent_urls.add(fallback)
                print(f"🟢 ارسال fallback موفق برای Tasnim")

        except Exception as f_err:
            print(f"❌ خطا در fallback Tasnim: {f_err}")
