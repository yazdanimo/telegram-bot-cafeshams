import json
import feedparser
import requests
from bs4 import BeautifulSoup
from telegram import InputMediaPhoto
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from googletrans import Translator
import hashlib
import os

# مسیر فایل‌ها
SOURCES_FILE = "data/sources.json"
SEEN_FILE = "data/seen.json"

# گروه سردبیری
EDITORIAL_CHAT_ID = -1002514471809

# تابع کمکی: استخراج خلاصه
def summarize(text, sentences_count=2):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join(str(sentence) for sentence in summary)

# تابع کمکی: ترجمه با Google Translate
translator = Translator()
def translate(text, dest="fa"):
    try:
        return translator.translate(text, dest=dest).text
    except:
        return text

# تابع کمکی: گرفتن تصویر اول خبر از HTML
def extract_image_from_url(url):
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        image = soup.find("meta", property="og:image")
        if image and image["content"]:
            return image["content"]
    except:
        return None

# تابع اصلی: دریافت و ارسال اخبار جدید
async def fetch_and_send_news(app):
    try:
        # بارگذاری منابع و خبرهای قبلاً دیده‌شده
        sources = json.load(open(SOURCES_FILE, encoding="utf-8"))
        seen = set(json.load(open(SEEN_FILE))) if os.path.exists(SEEN_FILE) else set()
        new_seen = set()

        for source in sources:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries:
                uid = hashlib.md5(entry.link.encode()).hexdigest()
                if uid in seen:
                    continue

                # دریافت اطلاعات اولیه خبر
                title = entry.title
                summary = entry.summary if "summary" in entry else ""
                link = entry.link
                content = f"{title}\n{summary}\n{link}"
                lang = "en" if any(ord(c) < 128 for c in content) else "fa"

                # خلاصه‌سازی و ترجمه در صورت نیاز
                if lang == "en":
                    short = summarize(summary)
                    translated = translate(f"{title}\n{short}", dest="fa")
                elif lang != "fa":
                    translated = translate(content, dest="en")
                    short = summarize(translated)
                    translated = translate(f"{title}\n{short}", dest="fa")
                else:
                    short = summarize(summary)
                    translated = f"{title}\n{short}"

                # استخراج تصویر خبر
                image_url = extract_image_from_url(link)
                caption = f"{source['name']} | {translated}\n\n🔗 {link}"

                # ارسال به تلگرام
                if image_url:
                    await app.bot.send_photo(chat_id=EDITORIAL_CHAT_ID, photo=image_url, caption=caption[:1024])
                else:
                    await app.bot.send_message(chat_id=EDITORIAL_CHAT_ID, text=caption)

                new_seen.add(uid)

        # ذخیره شناسه خبرهای دیده‌شده
        json.dump(list(seen.union(new_seen)), open(SEEN_FILE, "w"))

    except Exception as e:
        print(f"❌ خطا در fetch_and_send_news: {e}")
        await app.bot.send_message(chat_id=EDITORIAL_CHAT_ID, text=f"⚠️ خطا در ارسال خبر: {e}")
