import os
import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = os.getenv("TOKEN", "توکن-ربات-را-اینجا-بگذارید")
CHAT_ID = os.getenv("CHAT_ID", "آی‌دی-گروه-یا-کانال")

bot = Bot(token=TOKEN)

async def main_loop():
    sent_urls = set()
    while True:
        await fetch_and_send_news(bot, CHAT_ID, sent_urls)
        await asyncio.sleep(10 * 60)  # هر ۱۰ دقیقه یکبار اجرا

if __name__ == "__main__":
    asyncio.run(main_loop())
