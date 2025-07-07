import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID = "-1002514471809"
bot = Bot(token=TOKEN)

async def run_bot():
    sent_urls = set()
    await fetch_and_send_news(bot, CHAT_ID, sent_urls)

if __name__ == "__main__":
    asyncio.run(run_bot())
