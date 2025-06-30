import os
import json
import asyncio
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

GROUP_ID = -1002514471809  # آیدی عددی گروه سردبیری
TOKEN = os.getenv("BOT_TOKEN")

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

async def scheduled_job():
    try:
        await fetch_and_send_news(sources, bot, GROUP_ID)
    except Exception as e:
        print(f"خطا در scheduled_job: {e}")

async def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    global bot
    bot = application.bot

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", seconds=60, max_instances=1, coalesce=True)
    scheduler.start()

    print("🚀 ربات در حال اجراست...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    loop.run_forever()
