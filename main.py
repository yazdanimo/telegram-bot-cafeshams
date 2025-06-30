import os
import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1002514471809"))

bot = Bot(token=TOKEN)

async def start(update, context):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

async def scheduled_job():
    await fetch_and_send_news(bot, GROUP_ID)

async def setup():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", seconds=60)
    scheduler.start()

    print("🚀 ربات در حال اجراست...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(setup())
loop.run_forever()