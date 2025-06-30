import asyncio
import logging
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_and_send_news
import nest_asyncio
import os

# فعال‌سازی لاگ‌ها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# دریافت توکن از متغیر محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("توکن ربات در متغیر BOT_TOKEN یافت نشد.")

# تعریف تابع main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # زمان‌بندی اجرای fetch
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send_news, 'interval', minutes=1, args=[app.bot])
    scheduler.start()

    logger.info("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling(close_loop=False)

# اجرای برنامه
if __name__ == '__main__':
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    except RuntimeError as e:
        logger.error(f"❌ خطا: {e}")
