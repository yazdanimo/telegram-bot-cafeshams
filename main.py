import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from fetch_news import fetch_and_send_news

# پیام ثبت اجرا
print("📡 شروع اجرای برنامه...")

# پاسخ به دستور start فقط در چت خصوصی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("✅ ربات خبری کافه شمس آماده است!")

# تابع تکرارشونده برای بررسی فیدها
async def run_periodically(bot, feed_urls):
    while True:
        await fetch_and_send_news(bot, feed_urls)
        await asyncio.sleep(15)

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    feed_urls = [
        "https://www.reutersagency.com/feed/?best-topics=top-news",  # نمونه. بقیه RSS ها را اضافه کن
    ]

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    async def start_bot():
        asyncio.create_task(run_periodically(app.bot, feed_urls))
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await app.updater.idle()

    asyncio.run(start_bot())
