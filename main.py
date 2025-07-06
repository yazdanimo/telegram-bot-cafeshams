import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

# 🔧 تنظیمات ربات
TOKEN = "توکن_ربات_اینجا"
CHAT_ID = "آی‌دی_کانال_یا_گروه"
INTERVAL = 60  # هر 3600 ثانیه (یک ساعت)

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
