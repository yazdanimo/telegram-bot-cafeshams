import feedparser
import json
import os
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from googletrans import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from telegram import Bot
from bs4 import BeautifulSoup
import nest_asyncio

# رفع محدودیت اجرای asyncio داخل Thread Scheduler
nest_asyncio.apply()

# دریافت توکن و آیدی گروه از محیط اجرا
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# ساختن آبجکت تلگرام و مترجم
bot = Bot(token=BOT_TOKEN)
translator = Translator()
stats_file = "stats.json"

# بارگذاری منابع خبری از فایل
with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

# بارگذاری آمار اخبار ارسال‌شده
try:
    with open(stats_file, "r", encoding="utf-8") as f:
        sent_stats = json.load(f)
except FileNotFoundError:
    print("⚠️ stats.json یافت نشد، ایجاد مجموعه خالی.")
    sent_stats = {}

# بررسی اینکه خبر قبلاً ارسال شده یا نه
def already_sent(title):
    return title in sent_stats

# ثبت خبر به عنوان ارسال‌شده
def mark_as_sent(title):
    sent_stats[title] = datetime.utcnow().isoformat()
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(sent_stats, f, ensure_ascii=False, indent=2)

# پاکسازی HTML
def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

# خلاصه‌سازی متن انگلیسی
def summarize_text(text, sentences_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join(str(sentence) for sentence in summary)
    except:
        return text

# ترجمه متن
def translate_text(text, dest="fa"):
    try:
        translated = translator.translate(text, dest=dest)
        return translated.text
    except:
        return text

# بدنه اصلی ارسال اخبار
async def send():
    for source in sources:
        print(f"📡 بررسی منبع: {source['name']} - {source['url']}")
        feed = feedparser.parse(source["url"])

        for entry in feed.entries[:3]:
            title = clean_html(entry.title).strip()
            link = entry.link

            if already_sent(title):
                continue

            description = clean_html(entry.get("summary", ""))
            content = f"{source['name']} | {title}\n\n"

            # اگر فارسی نیست، خلاصه و ترجمه شود
            if not any(c in description for c in "اآبپتثجچ"):
                summary = summarize_text(description)
                translation = translate_text(summary)
                content += f"📝 خلاصه: {summary}\n\n🌐 ترجمه:\n{translation}\n\n"
            else:
                content += f"{description}\n\n"

            content += link

            await bot.send_message(chat_id=GROUP_ID, text=content)
            mark_as_sent(title)

# تابع زمان‌بندی اجرای خبر
def fetch_and_send_news():
    asyncio.create_task(send())

# Scheduler برای اجرای هر 1 دقیقه
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_send_news, "interval", minutes=1)
scheduler.start()

print("✅ fetch_news.py فعال شد و هر 1 دقیقه بررسی می‌کند...")

# اجرای همیشگی برای حفظ Scheduler
asyncio.get_event_loop().run_forever()
