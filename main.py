import os
import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from fetch_news import fetch_new_articles

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update, context):
    await update.message.reply_text("سلام! ربات خبری کافه شمس فعال است ☕📰")

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("❌ BOT_TOKEN environment variable not set!")

    print("Starting bot...")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    async def fetch_and_send_news():
        while True:
            await fetch_new_articles(app)
            await asyncio.sleep(15)

    asyncio.create_task(fetch_and_send_news())

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
