import os
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_news

BOT_TOKEN = os.environ.get("BOT_TOKEN")
EDITORIAL_CHAT_ID = -1002514471809  # آیدی عددی گروه سردبیری

bot = Bot(token=BOT_TOKEN)

async def send_news():
    try:
        news_list = fetch_news()
        if not news_list:
            print("⚠️ خبری برای ارسال وجود ندارد.")
            return
        for news in news_list:
            text = f"📰 <b>{news['title']}</b>\n\n{news['summary']}\n\n🌐 <i>{news['source']}</i>\n🔗 {news['link']}"
            if news.get("image"):
                await bot.send_photo(
                    chat_id=EDITORIAL_CHAT_ID,
                    photo=news["image"],
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_message(
                    chat_id=EDITORIAL_CHAT_ID,
                    text=text,
                    parse_mode=ParseMode.HTML
                )
    except Exception as e:
        print(f"❌ خطا در ارسال خبر: {e}")

async def start():
    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_news, "interval", minutes=1)
    scheduler.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app_job = asyncio.create_task(app.run_polling())
    await app_job

if __name__ == "__main__":
    asyncio.run(start())
