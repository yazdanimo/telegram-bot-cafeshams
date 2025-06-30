import os
import json
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler

GROUP_ID = -1002514471809  # آیدی عددی گروه سردبیری
TOKEN = os.getenv("BOT_TOKEN")

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

async def scheduled_job(bot):
    await fetch_and_send_news(sources, bot, GROUP_ID)

async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    bot = application.bot

    # زمان‌بندی اجرای fetch_and_send_news هر ۶۰ ثانیه
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", seconds=60, args=[bot])
    scheduler.start()

    print("🚀 ربات در حال اجراست...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
