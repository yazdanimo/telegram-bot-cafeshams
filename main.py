import asyncio
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram import Update
from telegram.ext import CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_news
import os

GROUP_ID = -1002514471809  # گروه سردبیری
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات خبری کافه شمس آماده است!")

async def send_news(app):
    print("🚀 بررسی اخبار جدید...")
    news_items = fetch_news()
    for item in news_items:
        msg = f"🗞 {item['source']} | {item['title']}\n\n{item['summary']}\n🔗 {item['link']}"
        if item['image']:
            await app.bot.send_photo(chat_id=GROUP_ID, photo=item['image'], caption=msg)
        else:
            await app.bot.send_message(chat_id=GROUP_ID, text=msg)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Scheduler باید داخل main تعریف و اجرا بشه
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_news, 'interval', seconds=60, args=[app])
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
