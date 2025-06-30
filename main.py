import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_and_send_news

# تنظیم توکن و آیدی گروه از محیط یا به‌صورت پیش‌فرض
TOKEN = os.getenv("BOT_TOKEN") or "7957685811:AAGC3ruFWuHouVsbsPt6TiPSv15CTduoyxA"
CHAT_ID = int(os.getenv("CHAT_ID") or -1002514471809)

# دستور start
async def start(update, context):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

# تابعی که هر دقیقه اجرا می‌شود
async def fetch_and_send():
    await fetch_and_send_news(CHAT_ID)

# تابع اصلی
async def main():
    # ساخت اپلیکیشن تلگرام
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # راه‌اندازی زمان‌بندی
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send, "interval", seconds=60)
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")

    # اجرای ربات بدون بستن event loop
    await app.run_polling(close_loop=False)

# اجرای main
if __name__ == "__main__":
    asyncio.run(main())
