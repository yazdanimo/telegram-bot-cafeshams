import feedparser
import hashlib
import html
import re
import aiohttp
from bs4 import BeautifulSoup
from utils import async_translate, detect_language

async def fetch_summary(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")
                paragraphs = soup.find_all("p")
                text = " ".join(p.get_text() for p in paragraphs)
                return text[:500]
    except:
        return ""

def clean_text(text):
    return html.unescape(re.sub(r"\s+", " ", text)).strip()

def hash_news(title):
    return hashlib.md5(title.encode("utf-8")).hexdigest()

async def fetch_and_send_news(bot, chat_id):
    import json
    from datetime import datetime
    from telegram import InputMediaPhoto

    try:
        with open("sources.json", "r", encoding="utf-8") as f:
            sources = json.load(f)
    except Exception as e:
        print(f"Error loading sources: {e}")
        return

    sent_hashes = set()

    for source in sources:
        url = source["url"]
        name = source.get("name", "منبع ناشناس")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = clean_text(entry.title)
                link = entry.link
                uid = hash_news(title)

                if uid in sent_hashes:
                    continue

                sent_hashes.add(uid)

                summary = await fetch_summary(link)
                lang = detect_language(summary or title)

                if lang not in ["en", "fa"]:
                    summary = await async_translate(summary, target_lang="en")
                    lang = "en"

                if lang == "en":
                    summary = await async_translate(summary, target_lang="fa")

                image_url = ""
                if "media_content" in entry:
                    image_url = entry.media_content[0].get("url", "")
                elif "image" in entry:
                    image_url = entry.image.get("href", "")

                caption = f"<b>{name} | {title}</b>\n\n{summary}\n\n<a href='{link}'>مشاهده خبر</a>"

                if image_url:
                    try:
                        await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption, parse_mode="HTML")
                    except:
                        await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")
                else:
                    await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")
        except Exception as e:
            print(f"❗️ خطا در پردازش {url}: {e}")
