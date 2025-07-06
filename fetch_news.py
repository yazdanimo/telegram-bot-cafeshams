import requests
from bs4 import BeautifulSoup
from langdetect import detect
from translatepy import Translator
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils import extract_full_content, extract_image_from_html
import json
import asyncio

translator = Translator()
dead_sources = set()
weak_sources = set()

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

def is_incomplete(text):
    ends = ["...", "،", "برای گسترش", "در حالی که", "زیرا", "تا", "و", "که"]
    return any(text.strip().endswith(e) for e in ends)

def clean_incomplete_sentences(text):
    return "\n".join([line.strip() for line in text.split("\n") if len(line.strip()) > 30 and not is_incomplete(line)])

def fix_cutoff_translation(text):
    lines = text.split("\n")
    return "\n".join(lines[:-1]) if lines and is_incomplete(lines[-1]) else text

def translate_text(text):
    try:
        cleaned = clean_incomplete_sentences(text)
        translated = translator.translate(cleaned, "Persian").result
        return fix_cutoff_translation(translated)
    except:
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
    source_fail_count = {}

    for source in sources:
        name = source.get("name")
        url = source.get("url")
        category = source.get("category", "news")

        if category_filter and category != category_filter:
            continue

        try:
            res = requests.get(url, timeout=10, headers=headers)
            res.raise_for_status()
        except:
            print(f"❌ خطا در RSS {name}")
            dead_sources.add(name)
            continue

        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")
        print(f"\n📡 RSS {name} → {len(items)} خبر")

        failed = 0

        for item in items[:5]:
            link = item.link.text.strip() if item.link else ""
            if not link or link in sent_urls:
                continue

            title = item.title.text.strip() if item.title else "بدون عنوان"
            raw_html = item.description.text.strip() if item.description else ""
            image_url = extract_image_from_html(raw_html)
            full_text, _ = extract_full_content(link)

            if "404" in full_text or not full_text:
                print(f"❌ خطای دریافت محتوا از {link}")
                dead_sources.add(name)
                failed += 1
                continue

            if not assess_content_quality(full_text):
                print(f"⚠️ رد شد: متن ضعیف از {name}")
                failed += 1
                continue

            if any(x in full_text for x in ["تماس با ما", "فید خبر", "Privacy", "آرشیو", "404"]):
                print(f"⚠️ حذف محتوا قالب از {name}")
                failed += 1
                continue

            try:
                lang = detect(title + full_text)
                if lang == "en":
                    title = translate_text(title)
                    full_text = translate_text(full_text)
            except:
                pass

            clean_text = clean_incomplete_sentences(full_text)
            intro = extract_intro_paragraph(clean_text)

            caption = f"📡 خبرگزاری {name} ({category})\n{title}\n\n{intro}\n\n🆔 @cafeshamss\nکافه شمس ☕️🍪"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📖 ادامه خبر", url=link)]])

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024], reply_markup=keyboard)
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], reply_markup=keyboard)
                print(f"✅ ارسال موفق از {name}")
                sent_urls.add(link)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❗️ خطا در ارسال پیام: {e}")

        if failed >= 4:
            weak_sources.add(name)

    print(f"\n📊 مجموع ارسال‌شده‌ها: {len(sent_urls)}")
    if dead_sources:
        print(f"🗑 منابع مرده: {', '.join(dead_sources)}")
    if weak_sources:
        print(f"⚠️ منابع ضعیف: {', '.join(weak_sources)}")
