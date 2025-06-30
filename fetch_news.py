
import feedparser
import html
import hashlib
import re
import aiohttp
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
from utils import clean_text, fetch_url, async_translate, detect_language, summarize_text, download_image, is_duplicate
from telegram import InputMediaPhoto

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

sent_news = set()

async def fetch_and_send_news(sources, bot, group_id):
    for source in sources:
        url = source.get("url")
        name = source.get("name")
        language = source.get("language", "auto")

        if not url or not name:
            continue

        try:
            content = await fetch_url(url)
            feed = feedparser.parse(content)

            for entry in feed.entries:
                title = html.unescape(entry.get("title", "")).strip()
                link = entry.get("link", "").strip()
                summary = html.unescape(entry.get("summary", "")).strip()
                published = entry.get("published", "")
                unique_id = hashlib.sha256((title + link).encode()).hexdigest()

                if is_duplicate(unique_id):
                    continue

                page_html = await fetch_url(link)
                soup = BeautifulSoup(page_html, "html.parser")
                text = clean_text(soup.get_text())

                if len(text) < 200:
                    text += "\n" + summary

                lang = detect_language(text)
                if lang not in ["fa", "en"]:
                    text = await async_translate(text, target="en")

                if lang == "en":
                    text = await async_translate(text, target="fa")

                short_text = summarize_text(text)
                image_url = await download_image(soup)

                caption = f"{name} | {title}\n\n{short_text}\n\n[لینک خبر]({link})"

                try:
                    if image_url:
                        await bot.send_photo(chat_id=group_id, photo=image_url, caption=caption, parse_mode='Markdown')
                    else:
                        await bot.send_message(chat_id=group_id, text=caption, parse_mode='Markdown')

                    sent_news.add(unique_id)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"❗️ خطا در ارسال خبر: {e}")

        except Exception as e:
            print(f"❗️ خطا در پردازش {url}: {e}")
