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

# برای ذخیره لینک‌هایی که 404 شده‌اند
bad_links = set()

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    report = []

    for src in sources:
        name     = src.get("name", "بدون‌نام")
        rss_url  = src.get("rss")
        fallback = src.get("fallback")

        try:
            items = parse_rss(rss_url)
            if not items:
                raise Exception("هیچ خبری دریافت نشد")

            report.append({"name": name, "status": "success", "count": len(items)})

            for item in items[:3]:
                link = item.get("link")
                if not link or link in sent_urls or link in bad_links:
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=15) as res:
                            # اگر status کد غیر از 200 بود، skip کن و علامت بده
                            if res.status != 200:
                                bad_links.add(link)
                                report.append({
                                    "name": name,
                                    "status": "http_error",
                                    "error": f"{res.status} for {link}"
                                })
                                break

                            raw = await res.text()

                    title   = item.get("title", "")
                    full    = extract_full_content(raw)
                    summary = summarize_text(full)

                    if not is_persian(title + " " + summary):
                        title   = translate_text(title)
                        summary = translate_text(summary)

                    caption = format_news(name, title, summary, link)
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                    sent_urls.add(link)
                    await asyncio.sleep(3)

                except Exception as e:
                    report.append({
                        "name": name,
                        "status": "send_error",
                        "error": str(e)
                    })
                    continue

        except Exception as e:
            report.append({"name": name, "status": "error", "error": str(e)})

            # fallback
            if fallback:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(fallback, timeout=15) as res:
                            if res.status != 200:
                                raise Exception(f"{res.status} for fallback")
                            raw = await res.text()

                    title   = f"{name} - گزارش جایگزین"
                    full    = extract_full_content(raw)
                    summary = summarize_text(full)
                    caption = format_news(name, title, summary, fallback)
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                    report[-1]["status"] = "fallback"
                    await asyncio.sleep(3)

                except Exception as f_err:
                    report.append({
                        "name": name,
                        "status": "fallback_error",
                        "error": str(f_err)
                    })

    # ارسال گزارش نهایی
    lines = []
    for r in report:
        status = r["status"]
        if status == "success":
            lines.append(f"✅ <b>{r['name']}</b> → دریافت {r['count']} خبر")
        elif status == "fallback":
            lines.append(f"🟡 <b>{r['name']}</b> → استفاده از fallback")
        else:
            lines.append(f"❌ <b>{r['name']}</b> → <code>{r.get('error')}</code>")

    await bot.send_message(chat_id=chat_id, text="\n".join(lines)[:4096], parse_mode="HTML")
