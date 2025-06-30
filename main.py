import asyncio
import nest_asyncio
import logging
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_and_send_news
import os

# تنظیمات لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# استفاده از nest_asyncio برای جلوگیری از خطای event loop
nest_asyncio.apply()

# متغیرها
BOT_TOKEN = os.getenv("BOT_TOKEN") or "توکن_بات_تو_اینجا"
CHAT_ID = os.getenv("CHAT_ID") or -1002514471809  # آی‌دی گروه سردبیری

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # برنامه‌ریز زمان‌بندی
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send_news, "interval", seconds=60, args=[app.bot, CHAT_ID])
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
