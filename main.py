import os
import asyncio
import json
from telegram import Bot, error
from fetch_news import fetch_and_send_news

TOKEN            = os.environ["BOT_TOKEN"]
GROUP_ID         = int(os.environ["GROUP_ID"])
SENT_URLS_FILE   = "sent_urls.json"
SENT_HASHES_FILE = "sent_hashes.json"

def load_set(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_set(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

async def main_loop():
    bot = Bot(token=TOKEN)

    try:
        info = await bot.get_chat(GROUP_ID)
        print("✅ Chat found:", info.title or info.username)
    except error.BadRequest as e:
        print("❌ Chat not found:", e)
        return

    sent_urls   = load_set(SENT_URLS_FILE)
    sent_hashes = load_set(SENT_HASHES_FILE)

    while True:
        print("🔄 شروع دوره دریافت اخبار")
        try:
            await asyncio.wait_for(
                fetch_and_send_news(bot, GROUP_ID, sent_urls, sent_hashes),
                timeout=180
            )
        except asyncio.TimeoutError:
            print("⏱️ Timeout: fetch_and_send_news took too long")
        except Exception as e:
            print("❌ Execution error →", e)

        save_set(sent_urls, SENT_URLS_FILE)
        save_set(sent_hashes, SENT_HASHES_FILE)
        print("🕒 منتظر دوره بعدی (۱۸۰ ثانیه)\n")
        await asyncio.sleep(180)

if __name__ == "__main__":
    asyncio.run(main_loop())
