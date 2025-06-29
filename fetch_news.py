import json
import feedparser
import html
import requests
from bs4 import BeautifulSoup
from telegram import InputMediaPhoto

# فهرست منابع RSS برای شروع
RSS_SOURCES = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "IRNA": "https://irna.ir/rss.aspx?lang=fa&id=34",
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
            summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()

            text = f"<b>{source}</b> | {title}\n\n{summary}\n\n<a href='{link}'>مطالعه بیشتر</a>"

            try:
                # ارسال به تلگرام
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
