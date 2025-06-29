import json
import feedparser
import html
import requests
from bs4 import BeautifulSoup
from telegram import InputMediaPhoto
from langdetect import detect
from deep_translator import GoogleTranslator
from difflib import SequenceMatcher

# فهرست منابع خبری
RSS_SOURCES = {
    "Reuters": "http://feeds.reuters.com/reuters/topNews",
    "Associated Press": "https://apnews.com/rss",
    "AFP": "https://www.afp.com/en/rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "Bloomberg": "https://www.bloomberg.com/feed/podcast/etf-report.xml",
    "Channel NewsAsia": "https://www.channelnewsasia.com/rssfeeds/8395986",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "Deutsche Welle": "https://rss.dw.com/rdf/rss-fa-all",
    "IRNA": "https://irna.ir/rss.aspx?lang=fa&id=34",
    "Fars News": "https://www.farsnews.ir/rss",
    "Tasnim News": "https://www.tasnimnews.com/fa/rss/feed/0/0/0/",
    "Mehr News": "https://www.mehrnews.com/rss",
    "Russia Today": "https://www.rt.com/rss/news/",
    "China Daily": "https://www.chinadaily.com.cn/rss/china_rss.xml",
    "United Press International": "https://rss.upi.com/news/top_news.rss",
    "Anadolu Agency": "https://www.aa.com.tr/en/rss/default?cat=0",
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",
    "El Pais": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "France 24": "https://www.france24.com/en/rss",
    "Al-Araby Al-Jadeed": "https://www.alaraby.co.uk/english/rss",
    "The Washington Post": "https://feeds.washingtonpost.com/rss/world",
    "Hindustan Times": "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",
    "The Times of India": "https://timesofindia.indiatimes.com/rss.cms",
    "Newsweek": "https://www.newsweek.com/feed",
    "The Independent": "https://www.independent.co.uk/news/world/rss",
    "Le Matin": "https://www.lematin.ch/rss",
    "Corriere della Sera": "https://xml2.corriereobjects.it/rss/homepage.xml",
    "Süddeutsche Zeitung": "https://rss.sueddeutsche.de/rss/Topthemen"
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

def is_duplicate(title, sent_titles):
    for old_title in sent_titles:
        ratio = SequenceMatcher(None, title, old_title).ratio()
        if ratio > 0.85:  # شباهت بالا
            return True
    return False

def extract_image(entry):
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
    if 'links' in entry:
        for link in entry.links:
            if hasattr(link, 'type') and "image" in link.type:
                return link.href
    return None

def translate_if_not_fa_or_en(text):
    try:
        lang = detect(text)
        if lang not in ['fa', 'en']:
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

async def fetch_and_send_news(bot, group_id):
    sent = load_sent_news()
    sent_titles = list(sent.values())  # تیترهای قبلاً ارسال‌شده

    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            news_id = entry.get("id") or entry.get("link")
            if not news_id:
                continue

            title = html.unescape(entry.get("title", "❗️ تیتر یافت نشد"))
            if is_duplicate(title, sent_titles):
                continue

            link = entry.get("link", "")
            summary_html = entry.get("summary", "")
            summary = BeautifulSoup(summary_html, "html.parser").get_text().strip()

            # ترجمه اگر زبان غیر از فارسی یا انگلیسی بود
            title = translate_if_not_fa_or_en(title)
            summary = translate_if_not_fa_or_en(summary)

            image_url = extract_image(entry)
            text = f"<b>{source}</b> | {title}\n\n{summary}\n\n<a href='{link}'>مطالعه بیشتر</a>"

            try:
                if image_url:
                    await bot.send_photo(
                        chat_id=group_id,
                        photo=image_url,
                        caption=text[:1024],
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
                sent[news_id] = title
                save_sent_news(sent)
                sent_titles.append(title)

            except Exception as e:
                print(f"❌ خطا در ارسال خبر: {e}")
