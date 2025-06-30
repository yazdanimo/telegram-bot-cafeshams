import asyncio
import os
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import nest_asyncio

nest_asyncio.apply()  # رفع خطای event loop

TOKEN = os.getenv("BOT_TOKEN")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # اجرای اولیه
    await fetch_and_send_news(app)

    # زمان‌بندی هر دقیقه
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send_news, "interval", seconds=60, args=[app])
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")

    await app.run_polling()  # بدون بستن loop

# اجرا بدون asyncio.run
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
