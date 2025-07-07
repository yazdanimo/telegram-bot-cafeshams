from utils import load_sources
import aiohttp
from utils import (
    extract_full_content,
    extract_image_from_html,
    extract_video_link,
    assess_content_quality,
    translate_text
)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    report_lines = []

    for source in sources:
        name = source["name"]
        url = source["rss"]

        try:
            items = await parse_rss(url)
            report_lines.append(f"📡 RSS {name} → {len(items)} خبر")

            for item in items:
                link = item["link"]

                if link in sent_urls:
                    continue

                # دریافت HTML برای پردازش محتوا
                async with aiohttp.ClientSession() as session:
                    async with session.get(link, timeout=10) as res:
                        raw_html = await res.text()

                full_text = extract_full_content(raw_html)
                image_url = extract_image_from_html(raw_html)
                video_url = extract_video_link(raw_html)

                title = item["title"]
                if is_text_english(title + " " + full_text):
                    title = translate_text(title)
                    full_text = translate_text(full_text)

                caption = f"📰 {title}\n\n{full_text}\n🔗 {link}"

                # ارسال خبر
                await bot.send_message(chat_id=chat_id, text=caption[:4096])
                sent_urls.add(link)

        except Exception as e:
            report_lines.append(f"❌ خطا در {name}: {e}")

    report_text = "\n".join(report_lines)
    await bot.send_message(chat_id=chat_id, text=report_text[:4096])
