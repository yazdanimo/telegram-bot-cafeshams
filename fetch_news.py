import feedparser
import hashlib
import json
import os
import requests
from bs4 import BeautifulSoup
from utils import translate_text, get_language

SENT_NEWS_HASHES_FILE = "sent_news_hashes.json"

def load_sent_news_hashes():
    if os.path.exists(SENT_NEWS_HASHES_FILE):
        with open(SENT_NEWS_HASHES_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_news_hashes(hashes):
    with open(SENT_NEWS_HASHES_FILE, "w") as f:
        json.dump(list(hashes), f)

def hash_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def summarize_text(text, max_chars=400):
    text = text.strip().replace('\n', ' ')
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit('.', 1)[0] + '.'

def extract_image(entry):
    if 'media_content' in entry:
        return entry['media_content'][0].get('url', '')
    elif 'media_thumbnail' in entry:
        return entry['media_thumbnail'][0].get('url', '')
    elif 'summary' in entry:
        soup = BeautifulSoup(entry['summary'], 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img.get('src')
    return ''

def extract_text(entry):
    if 'summary' in entry:
        return BeautifulSoup(entry['summary'], 'html.parser').get_text()
    elif 'content' in entry and isinstance(entry['content'], list):
        return BeautifulSoup(entry['content'][0].get('value', ''), 'html.parser').get_text()
    return ''

async def fetch_and_send_news(bot, chat_id):
    sent_hashes = load_sent_news_hashes()

    with open("sources.json", "r", encoding="utf-8") as f:
        sources = json.load(f)

    for source in sources:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:5]:
            title = entry.get("title", "❗️ تیتر یافت نشد")
            link = entry.get("link", "")
            full_text = extract_text(entry)
            if not full_text:
                continue

            lang = get_language(full_text)
            if lang == "en":
                summary = summarize_text(full_text)
            translated = await async_translate(summary, target_lang="fa")
            elif lang == "fa":
                summary = summarize_text(full_text)
                translated = summary
            else:
                translated = translate_text(full_text, dest="en")
                summary = summarize_text(translated)
               translated = await async_translate(summary, target_lang="fa")

            hash_id = hash_text(title + summary)
            if hash_id in sent_hashes:
                continue

            sent_hashes.add(hash_id)
            save_sent_news_hashes(sent_hashes)

            image_url = extract_image(entry)
            caption = f"<b>{source['name']} | {title}</b>\n\n{translated}\n\n<a href='{link}'>مطالعه بیشتر</a>"

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption, parse_mode="HTML")
                else:
                    await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")
            except Exception as e:
                print(f"❗️ خطا در ارسال خبر: {e}")
