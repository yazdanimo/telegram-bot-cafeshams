import requests
from bs4 import BeautifulSoup
from langdetect import detect
from translatepy import Translator
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils import extract_full_content, extract_image_from_html, extract_video_link
import json
import asyncio
import datetime
from urllib.parse import urlparse

translator = Translator()
BRAND_TAG = "\n\n🆔 @cafeshamss\nکافه شمس ☕️🍪"

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

try:
    with open("source_profiles.json", "r", encoding="utf-8") as f:
        source_profiles = json.load(f)
except:
    source_profiles = {}

try:
    with open("broken_links.json", "r", encoding="utf-8") as f:
        broken_links = json.load(f)
except:
    broken_links = {}

blocked_domains = [
    "foreignaffairs.com", "brookings.edu", "carnegieendowment.org",
    "cnn.com/videos", "aljazeera.com/video", "theatlantic.com", "iran-daily.com"
]

def shorten_link(url):
    try:
        api = f"https://is.gd/create.php?format=simple&url={url}"
        res = requests.get(api, timeout=5)
        return res.text.strip() if res.status_code == 200 else url
    except:
        return url

def is_incomplete(text):
    bad_endings = ("...", "،", "زیرا", "در حالی که", "که", "تا", "و")
    return text.strip().endswith(bad_endings)

def clean_incomplete_sentences(text):
    lines = text.split("\n")
    return "\n".join([line.strip() for line in lines if len(line.strip()) >= 30 and not is_incomplete(line)])

def fix_cutoff_translation(text):
    lines = text.split("\n")
    return "\n".join(lines[:-1]) if lines and is_incomplete(lines[-1]) else text

def translate_text(text):
    try:
        cleaned = clean_incomplete_sentences(text)
        translated = translator.translate(cleaned, "Persian").result
        return fix_cutoff_translation(translated)
    except Exception as e:
        print(f"❌ خطا در ترجمه متن: {e}")
        return text[:400]

def extract_intro_paragraph(text):
    for para in text.split("\n"):
        if len(para.strip()) > 60 and not is_incomplete(para):
            return para.strip()
    return text.strip()[:300]

def assess_content_quality(text):
    paragraphs = [p for p in text.split("\n") if len(p.strip()) > 40]
    return len(text) >= 300 and len(paragraphs) >= 2

async def fetch_and_send_news(bot, chat_id, sent_urls, category_filter=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    health_report = {}

    for source in sources:
        name = source.get("name")
        url = source.get("url")
        category = source.get("category", "news")
        profile = source_profiles.get(name, {})
        fallback_mode = profile.get("mode") == "fallback"
        title_only_mode = profile.get("mode") == "title_only"

        if category_filter and category != category_filter:
            continue

        try:
            res = requests.get(url, timeout=10, headers=headers)
            res.raise_for_status()
        except:
            print(f"❌ خطا در RSS {name}")
            health_report[name] = {"total": 0, "success": 0, "failed": 1}
            continue

        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")
        print(f"\n📡 RSS {name} → {len(items)} خبر")

        failed = 0
        success_count = 0

        for item in items[:8]:
            link = item.link.text.strip() if item.link else ""
            if not link or link in sent_urls or broken_links.get(link):
                continue

            domain = urlparse(link).netloc.lower()
            if any(blocked in domain or blocked in link for blocked in blocked_domains):
                print(f"🚫 لینک مسدود: {link}")
                failed += 1
                broken_links[link] = {
                    "source": name,
                    "status": "blocked",
                    "date": str(datetime.datetime.now())
                }
                continue

            title = item.title.text.strip() if item.title else "بدون عنوان"
            raw_html = item.description.text.strip() if item.description and item.description.text else ""
            image_url = extract_image_from_html(raw_html)
            video_url = extract_video_link(raw_html)
            full_text, _ = extract_full_content(link)
            short_link = shorten_link(link)

            if "404" in full_text or not full_text:
                broken_links[link] = {
                    "source": name,
                    "status": "404",
                    "date": str(datetime.datetime.now())
                }

                if title_only_mode:
                    caption = f"📡 خبر از {name}\n🎙️ {title}\n🔗 {short_link}{BRAND_TAG}"
                    await bot.send_message(chat_id=chat_id, text=caption[:4096])
                    sent_urls.add(link)
                    success_count += 1
                    continue
                elif fallback_mode:
                    intro = raw_html[:300] if raw_html else f"📌 لینک خبر: {short_link}"
                    caption = f"📡 خبر از {name}\n🎙️ {title}\n📝 {intro}\n🔗 {short_link}{BRAND_TAG}"
                    await bot.send_message(chat_id=chat_id, text=caption[:4096])
                    sent_urls.add(link)
                    success_count += 1
                    continue
                else:
                    print(f"❌ رد کامل از {name}")
                    failed += 1
                    continue

            if not assess_content_quality(full_text):
                print(f"⚠️ متن ضعیف از {name}")
                failed += 1
                broken_links[link] = {
                    "source": name,
                    "status": "weak",
                    "date": str(datetime.datetime.now())
                }
                continue

            try:
                lang = detect((title + " " + full_text).strip())
                if lang == "en":
                    title = translate_text(title).strip()
                    full_text = translate_text(full_text).strip()
            except Exception as e:
                print(f"❌ خطا در ترجمه از {name}: {e}")

            intro = extract_intro_paragraph(full_text)
            caption = f"📡 خبر از {name} ({category})\n🎙️ {title}\n\n📝 {intro}{BRAND_TAG}"

            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📖 مشاهده در منبع", url=short_link)]])
            if video_url:
                keyboard.inline_keyboard.append([InlineKeyboardButton("🎥 مشاهده ویدیو", url=video_url)])

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024], reply_markup=keyboard)
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], reply_markup=keyboard)
                sent_urls.add(link)
                success_count += 1
                await asyncio.sleep(2)
            except:
                failed += 1

        health_report[name] = {
            "total": len(items),
            "success": success_count,
            "failed": failed
        }

    # ذخیره لینک‌های خراب برای جلوگیری از ارسال تکراری
    try:
        with open("broken_links.json", "w", encoding="utf-8") as f:
            json.dump(broken_links, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره broken_links.json: {e}")

    # ساخت داشبورد HTML از سلامت منابع
    html = "<html><head><meta charset='utf-8'><title>📊 گزارش منابع</title></head><body>"
    html += "<h2>📊 وضعیت منابع خبر</h2><table border='1' cellpadding='5' style='border-collapse:collapse'>"
    html += "<tr><th>منبع</th><th>کل</th><th>موفق</th><th>خطا</th></tr>"

    for name, stats in health_report.items():
        total = stats.get("total", 0)
        success = stats.get("success", 0)
        failed = stats.get("failed", 0)
        color = "#d4fcdc" if success > failed else "#fde4e1"
        html += f"<tr style='background:{color}'><td>{name}</td><td>{total}</td><td>{success}</td><td>{failed}</td></tr>"

    html += "</table><br><p>تاریخ گزارش: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "</p></body></html>"

    try:
        with open("source_dashboard.html", "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"❌ خطا در ذخیره source_dashboard.html: {e}")

    # ارسال خلاصه عملکرد منابع به تلگرام
    summary = ["📊 گزارش عملکرد منابع:\n"]
    for name, stats in health_report.items():
        success = stats.get("success", 0)
        failed = stats.get("failed", 0)
        summary.append(f"{name}: ✅ {success} | ❌ {failed}")

    report_text = "\n".join(summary) + BRAND_TAG
    await bot.send_message(chat_id=chat_id, text=report_text[:4096])
    
