import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

# 🔧 تنظیمات ربات
TOKEN = "توکن_ربات_تلگرام_اینجا"
CHAT_ID = "آی‌دی_گروه_یا_کانال"

async def run_bot():
    bot = Bot(token=TOKEN)
    sent_urls = set()
    await fetch_and_send_news(bot, CHAT_ID, sent_urls)

if __name__ == "__main__":
    asyncio.run(run_bot())
