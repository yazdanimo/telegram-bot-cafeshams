import asyncio
import os
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_news

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002514471809

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
    await app.run_polling()  # بدون بسته شدن loop

# نکته مهم: این قسمت فقط در محیط‌های خاص اجرا شود، نه Railway
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "already running" in str(e):
            # در Railway این راه‌حل ایمن‌تر است
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().create_task(main())
        else:
            raise e
