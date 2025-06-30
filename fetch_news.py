import os
import asyncio
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram.ext import CommandHandler
from fetch_news import fetch_and_send_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))  # آیدی عددی گروه سردبیری

async def start(update, context):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send_news, 'interval', seconds=60, args=[app, GROUP_ID])
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling(close_loop=False)

if __name__ == '__main__':
    asyncio.run(main())
