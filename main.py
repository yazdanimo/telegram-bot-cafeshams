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
        print("✅ شروع دریافت اخبار...")
        await fetch_and_send_news(bot, CHAT_ID, sent_urls)
        save_sent_urls(sent_urls)
        print("🕒 پایان یک دور اجرا، صبر برای دور بعد...")
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main_loop())
