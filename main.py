import os
import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = os.getenv("TOKEN", "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M")
CHAT_ID = os.getenv("CHAT_ID", "-1002514471809")

bot = Bot(token=TOKEN)

async def main_loop():
    sent_urls = set()
    while True:
        await fetch_and_send_news(bot, CHAT_ID, sent_urls)
        await asyncio.sleep(10 * 60)  # هر ۱۰ دقیقه یکبار اجرا

if __name__ == "__main__":
    asyncio.run(main_loop())
