# File: main.py

import os, asyncio, json
from telegram import Bot, error
from fetch_news import fetch_and_send_news

TOKEN       = os.environ["BOT_TOKEN"]
GROUP_ID    = int(os.environ["GROUP_ID"])
SENT_URLS   = "sent_urls.json"
SENT_HASHES = "sent_hashes.json"

def load_set(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_set(data, file):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

async def main_loop():
    bot = Bot(token=TOKEN)
    try:
        info = await bot.get_chat(GROUP_ID)
        print("✅ Chat found:", info.title or info.username)
    except error.BadRequest as e:
        print("❌ Chat not found! check GROUP_ID →", e)
        return

    sent_urls   = load_set(SENT_URLS)
    sent_hashes = load_set(SENT_HASHES)

    while True:
        print("✅ مرحله دریافت آغاز شد")
        try:
            await fetch_and_send_news(bot, GROUP_ID, sent_urls, sent_hashes)
        except Exception as e:
            print("❌ خطا →", e)
            try:
                await bot.send_message(GROUP_ID, f"⚠️ خطا در اجرا → {e}")
            except:
                pass

        save_set(sent_urls, SENT_URLS)
        save_set(sent_hashes, SENT_HASHES)
        await asyncio.sleep(200)

if __name__ == "__main__":
    asyncio.run(main_loop())
