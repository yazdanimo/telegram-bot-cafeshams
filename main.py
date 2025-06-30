from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_news
import os
import asyncio

GROUP_ID = -1002514471809
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

async def run():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # دستور start
    app.add_handler(CommandHandler("start", start))

    # زمان‌بندی
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_news, "interval", minutes=1, args=[app])
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.wait()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
