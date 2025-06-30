import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_and_send_news

TOKEN = os.getenv("BOT_TOKEN") or "توکن_ربات_تو_اینجا"
CHAT_ID = int(os.getenv("CHAT_ID") or -1002514471809)  # آیدی گروه سردبیری

async def start(update, context):
    await update.message.reply_text("✅ ربات خبری کافه شمس فعال است!")

async def fetch_and_send():
    await fetch_and_send_news(CHAT_ID)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send, "interval", seconds=60)
    scheduler.start()

    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling()

# نکته مهم: فقط این خط اجرا می‌شود بدون بسته شدن event loop
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            # برای Railway یا محیط‌هایی با event loop فعال، از nest_asyncio استفاده می‌کنیم
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise
