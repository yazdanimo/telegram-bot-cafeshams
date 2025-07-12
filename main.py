# File: main.py

import asyncio
import json
from telegram import Bot, error
from fetch_news import fetch_and_send_news

# ← این دو مقدار را با مقادیر واقعی‌ات جایگزین کن
TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"
CHAT_ID_NEWS = -1001234567890  

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

    # چک کردن صحیح بودن کانال/گروه
    try:
        info = await bot.get_chat(CHAT_ID_NEWS)
        print("✅ Chat found:", info.title or info.username)
    except error.BadRequest as e:
        print("❌ Chat not found! check CHAT_ID_NEWS →", e)
        return

    while True:
        print("✅ مرحله دریافت آغاز شد")
        try:
            await fetch_and_send_news(bot, CHAT_ID_NEWS, sent_urls)
        except Exception as e:
            print(f"❌ خطا در fetch_and_send_news → {e}")
            try:
                await bot.send_message(
                    chat_id=CHAT_ID_NEWS,
                    text=f"⚠️ اجرای خبر با خطا مواجه شد → {e}"
                )
            except Exception as ee:
                print("⚠️ خطا در ارسال پیام خطا →", ee)

        save_sent_urls(sent_urls)
        await asyncio.sleep(200)

if __name__ == "__main__":
    asyncio.run(main_loop())
