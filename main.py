import asyncio
import json
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID = "-1002514471809"

bot = Bot(token=TOKEN)

def load_sent_urls():
    try:
        with open("sent_urls.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_sent_urls(sent_urls):
    with open("sent_urls.json", "w") as f:
        json.dump(list(sent_urls), f)

async def main_loop():
    sent_urls = load_sent_urls()
    while True:
        print("✅ مرحله 1: شروع دریافت اخبار")
        try:
            await fetch_and_send_news(bot, CHAT_ID, sent_urls)
            print("✅ مرحله 2: دریافت و ارسال انجام شد")
        except Exception as e:
            print(f"❌ مرحله 2.5: خطا در fetch_and_send_news → {e}")
            await bot.send_message(chat_id=CHAT_ID, text=f"❗️ خطای دریافت اخبار → {e}")

        save_sent_urls(sent_urls)
        print("🕒 مرحله 3: پایان یک دور اجرا، انتظار برای دور بعدی")
        await bot.send_message(chat_id=CHAT_ID, text="🕒 ربات همه‌چی آماده‌ی دور بعدی هست")
        await asyncio.sleep(200)

if __name__ == "__main__":
    print("🚀 ربات همه‌چی در حال راه‌اندازی است")
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"❌ خطای اجرای اصلی → {e}")
