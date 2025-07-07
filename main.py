import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN   = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID = "-1002514471809"

bot = Bot(token=TOKEN)

async def main_loop():
    sent_urls = set()
    while True:
        print("✅ شروع دریافت و ارسال اخبار...")
        await fetch_and_send_news(bot, CHAT_ID, sent_urls)
        print("🕒 پایان یک دور اجرا. صبر برای اجرای بعدی...")
        await asyncio.sleep(600)  # هر ۱۰ دقیقه یک بار اجرا

if __name__ == "__main__":
    asyncio.run(main_loop())
