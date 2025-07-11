import asyncio
import json
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID_NEWS = "-1002514471809"

SENT_URLS_FILE = "sent_urls.json"

def load_sent_urls():
    try:
        with open(SENT_URLS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_sent_urls(sent_urls):
    with open(SENT_URLS_FILE, "w") as f:
        json.dump(list(sent_urls), f)

async def main_loop():
    bot = Bot(token=TOKEN)
    sent_urls = load_sent_urls()

    while True:
        try:
            print("✅ مرحله دریافت آغاز شد")
            await fetch_and_send_news(bot, CHAT_ID_NEWS, sent_urls)
        except Exception as e:
            print(f"❌ خطا در اجرا → {e}")
            await bot.send_message(chat_id=CHAT_ID_NEWS, text=f"⚠️ اجرای خبر با خطا مواجه شد → {e}")

        save_sent_urls(sent_urls)

        await bot.send_message(chat_id=CHAT_ID_NEWS, text="🕒 پایان دور اجرا، انتظار برای دور بعدی...")
        await asyncio.sleep(200)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"❌ خطای کلی در راه‌اندازی ربات → {e}")
