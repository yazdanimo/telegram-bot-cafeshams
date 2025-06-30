# main.py
import asyncio
import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler
from fetch_news import fetch_and_send_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1002514471809"))

async def start(update, context):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send_news, 'interval', seconds=60, args=[app.bot, GROUP_ID])
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
