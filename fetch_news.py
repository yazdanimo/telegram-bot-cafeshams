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

# بارگذاری لینک‌های خراب
def load_bad_links():
    if os.path.exists(BAD_LINKS_FILE):
        try:
            with open(BAD_LINKS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

# ذخیره لینک‌های خراب
def save_bad_links(bad_links):
    with open(BAD_LINKS_FILE, "w") as f:
        json.dump(list(bad_links), f)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    bad_links = load_bad_links()
    report = []

    for src in sources:
        name = src.get("name", "بدون‌نام")
        rss_url = src.get("rss")
        fallback = src.get("fallback")

        print(f"⏳ بررسی منبع: {name}")

        try:
            items = parse_rss(rss_url)
            if not items:
                raise Exception("هیچ خبری دریافت نشد")

            report.append({ "name": name, "status": "success", "count": len(items) })

            for item in items[:3]:
                link = item.get("link")
                if not link or link in sent_urls or link in bad_links:
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=15) as res:
                            if res.status != 200:
                                print(f"❌ لینک خراب ({res.status}): {link}")
                                bad_links.add(link)
                                report.append({
                                    "name": name,
                                    "status": "http_error",
                                    "error": f"{res.status} → {link}"
                                })
                                break
                            raw = await res.text()

                    title = item.get("title", "")
                    full_text = extract_full_content(raw)
                    summary = summarize_text(full_text)

                    if not is_persian(title + " " + summary):
                        title = translate_text(title)
                        summary = translate_text(summary)

                    caption = format_news(name, title, summary, link)
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                    print(f"✅ خبر ارسال شد: {link}")
                    sent_urls.add(link)
                    await asyncio.sleep(3)

                except Exception as e:
                    print(f"⚠️ خطا در ارسال → {link}: {e}")
                    report.append({ "name": name, "status": "send_error", "error": str(e) })
                    continue

        except Exception as e:
            print(f"⚠️ خطا در دریافت از {name} → {e}")
            report.append({ "name": name, "status": "error", "error": str(e) })

            if fallback:
                try:
                    print(f"🟡 تلاش با fallback برای {name}")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(fallback, timeout=15) as res:
                            if res.status != 200:
                                raise Exception(f"{res.status} → fallback")
                            raw = await res.text()

                    title = f"{name} - گزارش جایگزین"
                    full_text = extract_full_content(raw)
                    summary = summarize_text(full_text)
                    caption = format_news(name, title, summary, fallback)

                    await bot.send_message(chat_id=chat_id, text=caption[:4096], parse_mode="HTML")
                    report.append({ "name": name, "status": "fallback", "count": 1 })
                    await asyncio.sleep(3)

                except Exception as f_err:
                    print(f"❌ خطای fallback برای {name} → {f_err}")
                    report.append({ "name": name, "status": "fallback_error", "error": str(f_err) })

    # ذخیره لینک‌های خراب
    save_bad_links(bad_links)

    # گزارش نهایی
    lines = []
    for r in report:
        s = r["status"]
        if s == "success":
            lines.append(f"✅ <b>{r['name']}</b> → دریافت {r['count']} خبر")
        elif s == "fallback":
            lines.append(f"🟡 <b>{r['name']}</b> → استفاده از fallback")
        else:
            lines.append(f"❌ <b>{r['name']}</b> → <code>{r.get('error')}</code>")

    await bot.send_message(chat_id=chat_id, text="\n".join(lines)[:4096], parse_mode="HTML")
