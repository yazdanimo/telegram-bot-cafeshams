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

async def scheduled_job():
    await fetch_and_send_news(sources, bot, GROUP_ID)

async def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    global bot
    bot = application.bot

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", seconds=60)
    scheduler.start()

    print("🚀 ربات در حال اجراست...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    # برای همیشه منتظر بمان
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.get_event_loop().create_task(run_bot())
    asyncio.get_event_loop().run_forever()
