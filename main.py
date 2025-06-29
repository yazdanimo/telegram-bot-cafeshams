import asyncio, os, feedparser, aiohttp
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, JobQueue
from utils import fetch_url, extract_news_title_and_image
from news_sources import news_sources

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
EDITOR_GROUP_ID = int(os.getenv("EDITOR_GROUP_ID"))
SENT_LINKS = set()

async def send_news(context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        for source in news_sources:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:5]:
                link = entry.link
                if link in SENT_LINKS:
                    continue
                html = await fetch_url(session, link)
                title, image_url = await extract_news_title_and_image(html, source["name"])
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📎 مشاهده خبر", url=link)]])
                if image_url:
                    await context.bot.send_photo(chat_id=EDITOR_GROUP_ID, photo=image_url, caption=title, reply_markup=keyboard)
                else:
                    await context.bot.send_message(chat_id=EDITOR_GROUP_ID, text=title, reply_markup=keyboard)
                SENT_LINKS.add(link)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = JobQueue()
    job_queue.set_application(app)
    job_queue.run_repeating(send_news, interval=15, first=5)

    await app.initialize()
    await app.start()
    await job_queue.start()
    print("✅ ربات خبری کافه شمس آماده است!")

if __name__ == "__main__":
    asyncio.run(main())
