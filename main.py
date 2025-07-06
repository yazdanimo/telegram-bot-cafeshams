import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

# 🔧 تنظیمات ربات
TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID = "-1002514471809"
INTERVAL = 60  # هر 60 ثانیه (یک دقیقه)

async def run_bot():
    bot = Bot(token=TOKEN)
    sent_urls = set()
    while True:
        print("\n🚀 شروع دریافت و ارسال خبر...\n")
        await fetch_and_send_news(bot, CHAT_ID, sent_urls)
        print(f"\n⏳ استراحت {INTERVAL} ثانیه‌ای قبل از مرحله بعد\n")
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(run_bot())
