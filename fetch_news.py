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

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=BOT_TOKEN)
translator = Translator()
stats_file = "stats.json"

# بارگذاری منابع خبری
with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

# بارگذاری آمار بازدید
try:
    with open(stats_file, "r", encoding="utf-8") as f:
        sent_stats = json.load(f)
except FileNotFoundError:
    print("⚠️ stats.json یافت نشد، ایجاد مجموعه خالی.")
    sent_stats = {}

def translate_text(text, dest="fa"):
    try:
        translated = translator.translate(text, dest=dest)
        return translated.text
    except:
        return text

def summarize_text(text, sentences_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join([str(sentence) for sentence in summary])
    except:
        return text

def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

def already_sent(title):
    return title in sent_stats

def mark_as_sent(title):
    sent_stats[title] = datetime.utcnow().isoformat()
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(sent_stats, f, ensure_ascii=False, indent=2)

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
            content = f"{source['name']} | {title}\n\n{description[:500]}\n\n{link}"

            # اگر انگلیسی، ترجمه کن
            if not any(c in description for c in "اآبپتثجچ"):
                summary = summarize_text(description)
                content += "\n\n📝 خلاصه: " + summarize_text(description)
                content += "\n\n🌐 ترجمه:\n" + translate_text(summary)

            await bot.send_message(chat_id=GROUP_ID, text=content)
            mark_as_sent(title)

# زمان‌بندی اجرا هر 1 دقیقه
def fetch_and_send_news():
    asyncio.create_task(send())

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_send_news, "interval", minutes=1)
scheduler.start()
