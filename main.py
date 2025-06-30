import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram.ext import CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_news
import os

TOKEN = os.getenv("BOT_TOKEN")  # حتماً در Railway تنظیم شده باشد
GROUP_ID = -1002514471809       # آیدی عددی گروه سردبیری

async def start(update, context):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است.")

async def send_news():
    news_items = fetch_news()
    if not news_items:
        print("❌ خبری برای ارسال وجود ندارد.")
        return
    bot = Bot(token=TOKEN)
    for news in news_items:
        caption = f"📰 <b>{news['source']}</b> | <b>{news['title']}</b>\n\n{news['summary']}\n\n🔗 {news['link']}"
        try:
            if news["image"]:
                await bot.send_photo(chat_id=GROUP_ID, photo=news["image"], caption=caption, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=GROUP_ID, text=caption, parse_mode="HTML")
            print(f"✅ خبر ارسال شد: {news['title']}")
        except Exception as e:
            print(f"❌ خطا در ارسال خبر: {e}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_news, "interval", seconds=60)
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
