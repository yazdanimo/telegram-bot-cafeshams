import feedparser
import asyncio
import hashlib
from bs4 import BeautifulSoup
from langdetect import detect
from deep_translator import GoogleTranslator
import requests

sent_cache = set()

def summarize_text(text, max_chars=400):
    return text[:max_chars] + "..." if len(text) > max_chars else text

def get_image_from_entry(entry):
    if "media_content" in entry:
        return entry.media_content[0].get("url")
    elif "links" in entry:
        for link in entry.links:
            if link.get("type", "").startswith("image/"):
                return link.get("href")
    elif "summary" in entry:
        soup = BeautifulSoup(entry.summary, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    return None

def hash_entry(entry):
    text = entry.get("title", "") + entry.get("link", "")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def translate_to_english(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print(f"❗️خطا در ترجمه: {e}")
        return text

async def process_source(source, bot, group_id):
    try:
        name = source.get("name", "منبع نامشخص")
        url = source.get("url")
        print(f"📡 بررسی منبع: {name} → {url}")

        if not url:
            print(f"⚠️ آدرس منبع {name} خالی است.")
            return

        feed = feedparser.parse(url)
        if not feed.entries:
            print(f"⚠️ منبع {name} ورودی ندارد.")
            return

        entry = feed.entries[0]
        entry_id = hash_entry(entry)
        if entry_id in sent_cache:
            print(f"⏭ خبر تکراری در منبع {name}")
            return

        sent_cache.add(entry_id)

        title = entry.get("title", "بدون عنوان")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        clean_text = BeautifulSoup(summary, "html.parser").get_text()
        lang = detect_language(clean_text)

        if lang not in ["fa", "en"]:
            print(f"🌐 زبان خبر {lang} → در حال ترجمه...")
            clean_text = translate_to_english(clean_text)
            title = translate_to_english(title)

        short_text = summarize_text(clean_text)
        image_url = get_image_from_entry(entry)

        caption = f"<b>{name}</b>\n<b>{title}</b>\n\n{short_text}\n\n{link}"

        if image_url:
            await bot.send_photo(chat_id=group_id, photo=image_url, caption=caption[:1024], parse_mode="HTML")
        else:
            await bot.send_message(chat_id=group_id, text=caption, parse_mode="HTML")

        print(f"✅ خبر ارسال شد از {name}")

    except Exception as e:
        print(f"❗️خطا در منبع {source.get('name')}: {e}")

async def fetch_and_send_news(sources, bot, group_id):
    tasks = []
    print(f"🔍 شروع بررسی {len(sources)} منبع خبری...")
    for source in sources:
        tasks.append(process_source(source, bot, group_id))
    await asyncio.gather(*tasks)
    print("✅ بررسی همه منابع تمام شد.")
