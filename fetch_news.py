import feedparser
import hashlib
import json
import os
from telegram import InputMediaPhoto
from telegram.constants import ParseMode

SEEN_HASHES_FILE = "data/stats.json"
CHAT_ID = -1002514471809  # گروه سردبیری

# بارگذاری هش خبرهای دیده‌شده
if os.path.exists(SEEN_HASHES_FILE):
    with open(SEEN_HASHES_FILE, "r") as f:
        seen_hashes = set(json.load(f))
else:
    seen_hashes = set()

def save_seen_hashes():
    with open(SEEN_HASHES_FILE, "w") as f:
        json.dump(list(seen_hashes), f)

def get_article_hash(entry):
    h = hashlib.sha256()
    h.update((entry.title + entry.link).encode("utf-8"))
    return h.hexdigest()

async def fetch_and_send_news(bot, feed_urls):
    for url in feed_urls:
        feed = feedparser.parse(url)
        source = feed.feed.get("title", "خبرگزاری نامشخص")
        for entry in feed.entries[:5]:  # حداکثر ۵ خبر اول هر منبع
            article_hash = get_article_hash(entry)
            if article_hash in seen_hashes:
                continue
            seen_hashes.add(article_hash)

            title = entry.title
            link = entry.link
            summary = entry.get("summary", "")
            image_url = None

            # پیدا کردن تصویر (از media:content یا enclosure)
            if "media_content" in entry:
                image_url = entry.media_content[0].get("url")
            elif "links" in entry:
                for l in entry.links:
                    if l.get("type", "").startswith("image/"):
                        image_url = l.get("href")
                        break

            caption = f"📰 <b>{source}</b> | <b>{title}</b>\n\n{summary[:500]}...\n\n🔗 <a href=\"{link}\">ادامه خبر</a>"

            try:
                if image_url:
                    await bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=image_url,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=caption,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False
                    )
            except Exception as e:
                print(f"❌ خطا در ارسال خبر: {e}")

    save_seen_hashes()
