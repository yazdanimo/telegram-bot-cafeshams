import os
import asyncio
from telegram import Bot, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from fetch_news import fetch_news
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002514471809

bot = Bot(token=BOT_TOKEN)

def format_message(news):
    text = f"🗞 <b>{news['source']}</b>\n\n"
    text += f"<b>{news['title']}</b>\n\n"
    text += f"{news['summary']}\n\n"
    return text.strip()

def build_keyboard(news):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 خواندن کامل خبر", url=news['link'])]
    ])

async def send_news():
    news_list = fetch_news()
    for news in news_list:
        try:
            text = format_message(news)
            keyboard = build_keyboard(news)
            if news["image"]:
                await bot.send_photo(
                    chat_id=GROUP_ID,
                    photo=news["image"],
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_message(
                    chat_id=GROUP_ID,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ ارسال ناموفق: {e}")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_news, "interval", minutes=1)
    scheduler.start()
    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
