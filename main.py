import asyncio
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID = "-1002514471809"

bot = Bot(token=TOKEN)

async def main_loop():
    print("✅ مرحله 1: اجرای main_loop آغاز شد")
    sent_urls = set()

    while True:
        print("✅ مرحله 2: فراخوانی fetch_and_send_news")
        try:
            await fetch_and_send_news(bot, CHAT_ID, sent_urls)
            print("✅ مرحله 3: پایان موفقیت‌آمیز fetch_and_send_news")
        except Exception as e:
            print(f"❌ مرحله 2.5: خطا در fetch_and_send_news → {e}")

        print("🕒 مرحله 4: صبر 10 دقیقه برای اجرای بعدی")
        await asyncio.sleep(600)

if __name__ == "__main__":
    print("🚀 مرحله 0: اجرای برنامه آغاز شد")
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"❌ مرحله 0.5: خطای اجرای اصلی → {e}")
