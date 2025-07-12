# File: main.py

import asyncio
import json
from telegram import Bot
from fetch_news import fetch_and_send_news

TOKEN = "توکن_ربات"
CHAT_ID_NEWS = "-100xxxxxxxxxx"
SENT_URLS_FILE = "sent_urls.json"

def load_sent_urls():
    try:
        with open(SENT_URLS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_sent_urls(sent_urls):
    with open(SENT_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_urls), f, ensure_ascii=False, indent=2)

async def main_loop():
    bot = Bot(token=TOKEN)
    sent_urls = load_sent_urls()

    while True:
        print("✅ مرحله دریافت آغاز شد")
        try:
            await fetch_and_send_news(bot, CHAT_ID_NEWS, sent_urls)
        except Exception as e:
            print(f"❌ خطا در fetch_and_send_news → {e}")
            try:
                await bot.send_message(chat_id=CHAT_ID_NEWS,
                    text=f"⚠️ اجرای خبر با خطا مواجه شد → {e}")
            except:
                pass
        save_sent_urls(sent_urls)
        await asyncio.sleep(200)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"❌ خطای کلی در راه‌اندازی ربات → {e}")
