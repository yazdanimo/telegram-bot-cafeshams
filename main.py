import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = "توکن ربات"
CHAT_ID = "شناسه گروه یا کانال"
bot = Bot(token=TOKEN)

async def run_bot():
    sent_urls = set()
    await fetch_and_send_news(bot, CHAT_ID, sent_urls)

if __name__ == "__main__":
    asyncio.run(run_bot())
