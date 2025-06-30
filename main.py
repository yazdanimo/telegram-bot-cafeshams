import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_news

# تنظیمات اولیه
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7957685811:AAGC3ruFWuHouVsbsPt6TiPSv15CTduoyxA"
GROUP_ID = -1002514471809  # گروه سردبیری

# دستور استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

# ارسال اخبار
async def send_news():
    logging.info("📡 در حال بررسی اخبار...")
    news_items = fetch_news()
    for item in news_items:
        message = f"📰 {item['title']}\n\n🌐 {item['source']}\n🔗 {item['link']}"
        await app.bot.send_message(chat_id=GROUP_ID, text=message)

# ساخت اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

# زمان‌بندی ارسال خبر هر یک دقیقه
scheduler = AsyncIOScheduler()
scheduler.add_job(send_news, "interval", minutes=1)
scheduler.start()

# اجرای ربات
if __name__ == "__main__":
    app.run_polling()
