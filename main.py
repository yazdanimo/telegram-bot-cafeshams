# File: main.py

import os
import asyncio
import json
from telegram import Bot, error
from fetch_news import fetch_and_send_news

# نام متغیر محیطی توکن را مطابق تنظیمات شما نگه‌داشته‌ایم
TOKEN    = os.environ["TOKEN"]
GROUP_ID = int(os.environ["GROUP_ID"])

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

    # اطمینان از وجود چت
    try:
        info = await bot.get_chat(GROUP_ID)
        print("✅ Chat found:", info.title or info.username)
    except error.BadRequest as e:
        print("❌ Chat not found! check GROUP_ID →", e)
        return

    while True:
        print("✅ مرحله دریافت آغاز شد")
        try:
            await fetch_and_send_news(bot, GROUP_ID, sent_urls)
        except Exception as e:
            print(f"❌ خطا در fetch_and_send_news → {e}")
            try:
                await bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"⚠️ اجرای خبر با خطا مواجه شد → {e}"
                )
            except Exception as ee:
                print("⚠️ خطا در ارسال پیام خطا →", ee)
        save_sent_urls(sent_urls)
        await asyncio.sleep(200)

if __name__ == "__main__":
    asyncio.run(main_loop())
