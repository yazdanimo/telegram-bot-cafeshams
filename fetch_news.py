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
    parse_rss,
    shorten_url
)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    report_results = []

    for source in sources:
        name = source.get("name", "بدون‌نام")
        rss_url = source.get("rss")
        fallback_url = source.get("fallback")  # در صورت نیاز به منبع جایگزین

        try:
            items = parse_rss(rss_url)
            if not items:
                raise Exception("هیچ خبری دریافت نشد")

            report_results.append({ "name": name, "status": "success", "count": len(items) })

            for item in items[:5]:  # برای جلوگیری از flood فقط ۵ خبر اول
                link = item.get("link")
                if not link or link in sent_urls:
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=15) as res:
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
                    print(f"⚠️ خطا در ارسال خبر → {link}: {e}")
                    continue

        except Exception as e:
            # تلاش بازیابی با fallback
            if fallback_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(fallback_url, timeout=15) as res:
                            html = await res.text()
                            title = f"{name} - گزارش جایگزین"
                            full_text = extract_full_content(html)
                            summary = summarize_text(full_text)
                            short_link = shorten_url(fallback_url)
                            caption = format_news(name, title, summary, short_link)
                            await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                            report_results.append({ "name": name, "status": "fallback", "count": 1 })
                            continue
                except Exception as fallback_error:
                    report_results.append({ "name": name, "status": "error", "error": str(fallback_error) })
            else:
                report_results.append({ "name": name, "status": "error", "error": str(e) })

    # گزارش نهایی زیبا
    report_lines = []
    for r in report_results:
        if r["status"] == "success":
            report_lines.append(f"✅ <b>{r['name']}</b> → دریافت {r['count']} خبر")
        elif r["status"] == "fallback":
            report_lines.append(f"🟡 <b>{r['name']}</b> → دریافت جایگزین با fallback")
        else:
            report_lines.append(f"❌ <b>{r['name']}</b> → {r['error']}")

    await bot.send_message(chat_id=chat_id, text="\n".join(report_lines)[:4096], parse_mode="HTML")
