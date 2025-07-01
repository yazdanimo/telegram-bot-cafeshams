import os
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

# آیدی گروه پشتیبانی (سردبیری)
GROUP_CHAT_ID = -1002514471809

# ذخیره لینک‌های ارسال‌شده
sent_urls = set()

async def scheduled_job(application):
    global sent_urls
    print("🔄 اجرای scheduled_job در حال انجام است...")
    try:
        sent_urls = await fetch_and_send_news(application.bot, GROUP_CHAT_ID, sent_urls)
    except Exception as e:
        print(f"❗️ خطا در اجرای scheduled_job: {e}")

async def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # اجرای job هر ۱۵ ثانیه
    async def run_scheduler():
        while True:
            await scheduled_job(app)
            await asyncio.sleep(15)

    asyncio.create_task(run_scheduler())
    print("🚀 ربات در حال اجراست...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
