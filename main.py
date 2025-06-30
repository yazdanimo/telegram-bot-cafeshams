import os
import json
import asyncio
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_and_send_news

GROUP_ID = -1002514471809
TOKEN = os.getenv("BOT_TOKEN")

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

async def scheduled_job(bot):
    try:
        print("🔄 در حال اجرای scheduled_job...")
        await fetch_and_send_news(sources, bot, GROUP_ID)
    except Exception as e:
        print(f"❗️خطا در scheduled_job: {e}")

async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    bot = application.bot

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", seconds=60, args=[bot], max_instances=1, coalesce=True)
    scheduler.start()

    print("🚀 ربات خبری کافه شمس در حال اجراست...")
    await application.run_polling()

# ✅ به جای asyncio.run(...) از این استفاده کن:
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
