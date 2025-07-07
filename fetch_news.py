import aiohttp
from utils import (
    load_sources,
    extract_full_content,
    extract_image_from_html,
    extract_video_link,
    summarize_text,
    format_news,
    translate_text,
    is_text_english,
    parse_rss
)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    report_lines = []

    for source in sources:
        name = source.get("name", "بدون‌نام")
        url = source.get("rss")
        if not url:
            report_lines.append(f"⚠️ rss ناموجود برای {name}")
            continue

        try:
            items = parse_rss(url)
            report_lines.append(f"📡 RSS {name} → {len(items)} خبر")

            for item in items:
                link = item.get("link")
                if not link or link in sent_urls:
                    continue

                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as res:
                        raw_html = await res.text()

                title = item.get("title", "")
                full_text = extract_full_content(raw_html)
                summary = summarize_text(full_text)

                if is_text_english(title + " " + full_text):
                    title = translate_text(title)
                    summary = translate_text(summary)

                caption = format_news(name, title, summary, link)

                await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                sent_urls.add(link)

        except Exception as e:
            report_lines.append(f"❌ خطا در {name}: {e}")

    await bot.send_message(chat_id=chat_id, text="\n".join(report_lines)[:4096])
