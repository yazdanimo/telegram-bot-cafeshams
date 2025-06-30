import feedparser
import asyncio
import hashlib
from bs4 import BeautifulSoup
import requests

sent_cache = set()  # جلوگیری از ارسال تکراری

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

async def fetch_and_send_news(sources, bot, group_id):
    for source in sources:
        try:
            url = source.get("url")
            name = source.get("name", "منبع نامشخص")
            if not url:
                continue

            feed = feedparser.parse(url)
            if not feed.entries:
                continue

            entry = feed.entries[0]
            entry_id = hash_entry(entry)
            if entry_id in sent_cache:
                continue  # جلوگیری از ارسال تکراری

            sent_cache.add(entry_id)

            title = entry.get("title", "بدون عنوان")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            clean_text = BeautifulSoup(summary, "html.parser").get_text()
            short_text = summarize_text(clean_text)

            image_url = get_image_from_entry(entry)

            caption = f"<b>{name}</b>\n<b>{title}</b>\n\n{short_text}\n\n{link}"

            if image_url:
                await bot.send_photo(chat_id=group_id, photo=image_url, caption=caption[:1024], parse_mode="HTML")
            else:
                await bot.send_message(chat_id=group_id, text=caption, parse_mode="HTML")

            await asyncio.sleep(1)

        except Exception as e:
            print(f"❗️خطا در منبع {source.get('name')}: {e}")
