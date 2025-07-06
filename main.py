import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

# 🔧 تنظیمات ربات
TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID = "-1002514471809"

async def run_bot():
    bot = Bot(token=TOKEN)
    sent_urls = set()
    await fetch_and_send_news(bot, CHAT_ID, sent_urls)

if __name__ == "__main__":
    asyncio.run(run_bot())
