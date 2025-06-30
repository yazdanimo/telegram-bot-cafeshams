import os
import json
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler

GROUP_ID = -1002514471809
TOKEN = os.getenv("BOT_TOKEN")

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

async def scheduled_job():
    await fetch_and_send_news(sources, bot, GROUP_ID)

async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    global bot
    bot = application.bot

    # راه‌اندازی زمان‌بندی
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", seconds=60)
    scheduler.start()

    print("🚀 ربات در حال اجراست...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # اجرای بی‌نهایت
    await asyncio.Event().wait()

# اجرای مستقیم بدون run()
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print("⛔️ توقف دستی ربات")
