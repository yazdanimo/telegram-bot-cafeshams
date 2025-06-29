import json
import feedparser
import html
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from telegram import InputMediaPhoto

# منابع خبری حرفه‌ای (بین‌المللی و ایرانی)
RSS_SOURCES = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "http://feeds.reuters.com/reuters/topNews",
    "AP": "https://apnews.com/rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "Deutsche Welle": "https://rss.dw.com/rdf/rss-fa-all",
    "IRNA": "https://irna.ir/rss.aspx?lang=fa&id=34",
    "Fars": "https://www.farsnews.ir/rss",
    "Tasnim": "https://www.tasnimnews.com/fa/rss/feed/0/0/0/",
}

SENT_NEWS_FILE = "stats.json"

def load_sent_news():
    try:
        with open(SENT_NEWS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_sent_news(data):
    with open(SENT_NEWS_FILE, "w") as f:
        json.dump(data, f)

def translate_if_needed(text):
    if not text:
        return ""
    if any(ord(c) > 1500 for c in text):
        return text  # اگر متن فارسی باشد، نیازی به ترجمه نیست
    try:
        return GoogleTranslator(source='auto', target='fa').translate(text)
    except:
        return text  # اگر ترجمه شکست خورد، همان متن اصلی را برگردان

def extract_image(entry):
    # تلاش برای یافتن تصویر از RSS
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
    if 'links' in entry:
        for link in entry.links:
            if hasattr(link, 'type') and "image" in link.type:
                return link.href
    return None

async def fetch_and_send_news(bot, group_id):
    sent = load_sent_news()

    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            news_id = entry.get("id") or entry.get("link")
            if not news_id or news_id in sent:
                continue

            title = html.unescape(entry.get("title", "❗️ تیتر یافت نشد"))
            link = entry.get("link", "")
            summary_html = entry.get("summary", "")
            summary = BeautifulSoup(summary_html, "html.parser").get_text().strip()

            title_translated = translate_if_needed(title)
            summary_translated = translate_if_needed(summary)

            image_url = extract_image(entry)

            text = f"<b>{source}</b> | {title_translated}\n\n{summary_translated}\n\n<a href='{link}'>مطالعه بیشتر</a>"

            try:
                if image_url:
                    await bot.send_photo(
                        chat_id=group_id,
                        photo=image_url,
                        caption=text[:1024],  # محدودیت کپشن تلگرام
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=group_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
                print(f"✅ خبر ارسال شد: {source} | {title}")
                sent[news_id] = True
                save_sent_news(sent)

            except Exception as e:
                print(f"❌ خطا در ارسال خبر: {e}")
