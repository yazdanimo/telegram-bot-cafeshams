import os
import json
import asyncio
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update, Bot
from googletrans import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# بارگذاری توکن و گروه
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# ساختن ربات و مترجم
bot = Bot(token=BOT_TOKEN)
translator = Translator()
stats_file = "stats.json"

# منابع خبری
with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

# اخبار ارسال‌شده
try:
    with open(stats_file, "r", encoding="utf-8") as f:
        sent_stats = json.load(f)
except FileNotFoundError:
    print("📁 stats.json یافت نشد، ساخته می‌شود.")
    sent_stats = {}

# پاک کردن HTML
def clean_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

# خلاصه‌سازی
def summarize_text(text, sentences_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join(str(s) for s in summary)
    except:
        return text

# ترجمه
def translate_text(text, dest="fa"):
    try:
        return translator.translate(text, dest=dest).text
    except:
        return text

# بررسی ارسال‌شده بودن
def already_sent(title):
    return title in sent_stats

def mark_as_sent(title):
    sent_stats[title] = datetime.utcnow().isoformat()
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(sent_stats, f, ensure_ascii=False, indent=2)

# ارسال اخبار
async def send_news():
    for source in sources:
        print(f"📡 منبع: {source['name']} - {source['url']}")
        feed = feedparser.parse(source["url"])

        for entry in feed.entries[:3]:
            title = clean_html(entry.title).strip()
            link = entry.link

            if already_sent(title):
                continue

            description = clean_html(entry.get("summary", ""))
            content = f"{source['name']} | {title}\n\n"

            if not any(c in description for c in "اآبپتثجچ"):
                summary = summarize_text(description)
                translation = translate_text(summary)
                content += f"📝 خلاصه: {summary}\n\n🌐 ترجمه:\n{translation}\n\n"
            else:
                content += f"{description}\n\n"

            content += link

            await bot.send_message(chat_id=GROUP_ID, text=content)
            mark_as_sent(title)

# فرمان /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

# راه‌اندازی ربات و scheduler
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # زمان‌بندی ارسال اخبار
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_news, "interval", minutes=1)
    scheduler.start()

    print("✅ ربات در حال اجراست و هر ۱ دقیقه اخبار را بررسی می‌کند...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
