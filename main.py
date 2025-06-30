import os
import json
import asyncio
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update, Bot
from deep_translator import GoogleTranslator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=BOT_TOKEN)
stats_file = "stats.json"

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

try:
    with open(stats_file, "r", encoding="utf-8") as f:
        sent_stats = json.load(f)
except FileNotFoundError:
    print("📁 stats.json یافت نشد، ساخته می‌شود.")
    sent_stats = {}

def clean_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

def summarize_text(text, sentences_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join(str(s) for s in summary)
    except:
        return text

def translate_text(text, dest="fa"):
    try:
        return GoogleTranslator(source='auto', target=dest).translate(text)
    except:
        return text

def already_sent(title):
    return title in sent_stats

def mark_as_sent(title):
    sent_stats[title] = datetime.utcnow().isoformat()
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(sent_stats, f, ensure_ascii=False, indent=2)

async def send_news():
    for source in sources:
        print(f"📡 {source['name']}")
        feed = feedparser.parse(source["url"])

        for entry in feed.entries[:3]:
            title = clean_html(entry.title).strip()
            link = entry.link

            if already_sent(title):
                continue

            description = clean_html(entry.get("summary", ""))
            content = f"{source['name']} | {title}

"

            if not any(c in description for c in "اآبپتثجچ"):
                summary = summarize_text(description)
                translation = translate_text(summary)
                content += f"📝 خلاصه: {summary}

🌐 ترجمه:
{translation}

"
            else:
                content += f"{description}

"

            content += link

            await bot.send_message(chat_id=GROUP_ID, text=content)
            mark_as_sent(title)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات خبری فعال است!")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_news, "interval", minutes=1)
    scheduler.start()

    print("✅ ربات در حال اجراست...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())