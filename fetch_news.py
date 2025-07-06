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
dead_sources = set()
weak_sources = set()

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

try:
    with open("source_profiles.json", "r", encoding="utf-8") as f:
        source_profiles = json.load(f)
except:
    source_profiles = {}

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
    bad = ["...", "،", "برای گسترش", "در حالی که", "زیرا", "تا", "و", "که"]
    return any(text.strip().endswith(e) for e in bad)

def clean_incomplete_sentences(text):
    lines = text.split("\n")
    return "\n".join([l.strip() for l in lines if len(l.strip()) >= 30 and not is_incomplete(l)])

def fix_cutoff_translation(text):
    lines = text.split("\n")
    return "\n".join(lines[:-1]) if lines and is_incomplete(lines[-1]) else text

def translate_text(text):
    try:
        clean = clean_incomplete_sentences(text)
        translated = translator.translate(clean, "Persian").result
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
    paras = [p for p in text.split("\n") if len(p.strip()) > 40]
    return len(text) >= 300 and len(paras) >= 2

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
            dead_sources.add(name)
            health_report[name] = { "total": 0, "success": 0, "failed": 1 }
            continue

        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")
        print(f"\n📡 RSS {name} → {len(items)} خبر")

        failed = 0
        success_count = 0

        for item in items[:8]:
            link = item.link.text.strip() if item.link else ""
            if not link or link in sent_urls:
                continue

            domain = urlparse(link).netloc.lower()
            if any(blocked in domain or blocked in link for blocked in blocked_domains):
                print(f"🚫 لینک مسدود یا محافظت‌شده: {link}")
                failed += 1
                continue

            title = item.title.text.strip() if item.title else "بدون عنوان"
            raw_html = item.description.text.strip() if item.description and item.description.text else ""
            image_url = extract_image_from_html(raw_html)
            video_url = extract_video_link(raw_html)

            full_text, _ = extract_full_content(link)

            if "404" in full_text or not full_text:
                short_link = shorten_link(link)

                if title_only_mode:
                    caption = f"📡 خبر از {name}\n🎙️ {title}\n🔗 {short_link}\n🆔 @cafeshamss"
                    try:
                        await bot.send_message(chat_id=chat_id, text=caption[:4096])
                        sent_urls.add(link)
                        success_count += 1
                        print(f"📎 ارسال تیتر تنها از {name}")
                    except:
                        print(f"❌ ارسال تیتر شکست خورد از {name}")
                    continue

                elif fallback_mode:
                    intro = raw_html[:300] if raw_html else f"📌 لینک خبر: {short_link}"
                    caption = f"📡 خبر از {name}\n🎙️ {title}\n📝 {intro}\n🔗 {short_link}\n🆔 @cafeshamss"
                    try:
                        await bot.send_message(chat_id=chat_id, text=caption[:4096])
                        sent_urls.add(link)
                        success_count += 1
                        print(f"📎 ارسال با توضیح جایگزین از {name}")
                    except:
                        print(f"❌ ارسال fallback شکست خورد از {name}")
                    continue

                else:
                    print(f"❌ رد کامل از {name}")
                    failed += 1
                    continue

            if not assess_content_quality(full_text):
                print(f"⚠️ رد شد: متن ضعیف از {name}")
                failed += 1
                continue

            try:
                full_input = (title + " " + full_text).strip()
                lang = detect(full_input)

                if lang == "en":
                    print(f"🌐 تشخیص متن انگلیسی از {name}")
                    translated_title = translate_text(title)
                    translated_text = translate_text(full_text)

                    if translated_title and translated_text:
                        title = translated_title.strip()
                        full_text = translated_text.strip()
                        print(f"✅ ترجمه موفق از {name}")
                    else:
                        print(f"⚠️ ترجمه ناقص از {name}")
                else:
                    print(f"🌐 متن {name} به زبان {lang}")
            except Exception as e:
                print(f"❌ خطا در ترجمه یا تشخیص زبان از {name}: {e}")

            clean_text = clean_incomplete_sentences(full_text)
            intro = extract_intro_paragraph(clean_text)
            short_link = shorten_link(link)

            caption = (
                f"📡 خبر از {name} ({category})\n🎙️ {title}\n\n📝 {intro}\n🆔 @cafeshamss ☕️📡🍪"
            )

            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📖 مشاهده خبر در منبع", url=short_link)]])
            if video_url:
                keyboard.inline_keyboard.append([InlineKeyboardButton("🎥 مشاهده ویدیو", url=video_url)])

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024], reply_markup=keyboard)
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], reply_markup=keyboard)
                sent_urls.add(link)
                success_count += 1
                print(f"✅ ارسال موفق از {name}")
                await asyncio.sleep(2)
            except:
                failed += 1

        if failed >= 4:
            weak_sources.add(name)

        health_report[name] = {
            "total": len(items),
            "success": success_count,
            "failed": failed
        }

    date_key = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        with open("source_health.json", "w", encoding="utf-8") as f:
            json.dump({date_key: health_report}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره source_health.json: {e}")

    summary = ["📊 گزارش روزانه کافه شمس:\n"]
    for name, stats in health_report.items():
        success = stats.get("success", 0)
        failed = stats.get("failed", 0)
        summary.append(f"{name}: ✅ {success} | ❌ {failed}")

    await bot.send_message(chat_id=chat_id, text="\n".join(summary)
