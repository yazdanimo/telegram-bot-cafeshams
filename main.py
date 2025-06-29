import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from fetch_news import fetch_and_send_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROUP_ID = -1002514471809  # آیدی گروه سردبیری

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

async def news_loop(application):
    while True:
        try:
            await fetch_and_send_news(application.bot, GROUP_ID)
        except Exception as e:
            logger.error(f"❌ خطا در news_loop: {e}")
        await asyncio.sleep(15)

async def post_init(application):
    asyncio.create_task(news_loop(application))

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
