import aiohttp
import asyncio
from utils import (
    load_sources,
    extract_full_content,
    summarize_text,
    format_news,
    translate_text,
    is_persian,
    parse_rss
)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    report = []

    for src in sources:
        name = src.get("name", "بدون‌نام")
        rss_url = src.get("rss")
        fallback = src.get("fallback")

        try:
            items = parse_rss(rss_url)
            if not items:
                raise Exception("هیچ خبری دریافت نشد")

            report.append({"name": name, "status": "success", "count": len(items)})

            for item in items[:3]:
                link = item.get("link")
                if not link or link in sent_urls:
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=15) as res:
                            raw = await res.text()

                    title = item.get("title", "")
                    full = extract_full_content(raw)
                    summary = summarize_text(full)

                    # فقط متون غیر فارسی را ترجمه کن
                    if not is_persian(title + " " + summary):
                        title = translate_text(title)
                        summary = translate_text(summary)

                    caption = format_news(name, title, summary, link)
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                    sent_urls.add(link)
                    await asyncio.sleep(3)

                except Exception as e:
                    print(f"⚠️ خطا در ارسال خبر → {link}: {e}")
                    continue

        except Exception as e:
            report.append({"name": name, "status": "error", "error": str(e)})

            # تلاش با fallback اگر تعریف شده
            if fallback:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(fallback, timeout=15) as res:
                            raw = await res.text()

                    title = f"{name} - گزارش جایگزین"
                    full = extract_full_content(raw)
                    summary = summarize_text(full)
                    caption = format_news(name, title, summary, fallback)
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                    report[-1]["status"] = "fallback"
                    await asyncio.sleep(3)

                except Exception as f_err:
                    report.append({"name": name, "status": "fallback_error", "error": str(f_err)})

    # ارسال گزارش نهایی
    lines = []
    for r in report:
        if r["status"] == "success":
            lines.append(f"✅ <b>{r['name']}</b> → دریافت {r['count']} خبر")
        elif r["status"] == "fallback":
            lines.append(f"🟡 <b>{r['name']}</b> → استفاده از fallback")
        else:
            lines.append(f"❌ <b>{r['name']}</b> → <code>{r['error']}</code>")

    await bot.send_message(chat_id=chat_id, text="\n".join(lines)[:4096], parse_mode="HTML")
