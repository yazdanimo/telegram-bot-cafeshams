import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from fetch_news import fetch_and_send_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# اطلاعات اولیه
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002514471809  # آیدی عددی گروه سردبیری

# دستور /start
async def start(update, context):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است.")

# برنامه زمان‌بندی‌شده هر ۱ دقیقه
async def scheduled_job():
    from telegram import Bot
    bot = Bot(BOT_TOKEN)
    await fetch_and_send_news(bot, GROUP_ID)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # هندلر دستور start
    app.add_handler(CommandHandler("start", start))

    # زمان‌بندی اخبار
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", minutes=1)
    scheduler.start()

    print("🚀 ربات در حال اجراست...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
