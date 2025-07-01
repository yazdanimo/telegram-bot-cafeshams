import os
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

GROUP_CHAT_ID = -1002514471809
sent_urls = set()

async def scheduled_job(bot):
    global sent_urls
    print("🔄 اجرای scheduled_job در حال انجام است...")
    try:
        sent_urls = await fetch_and_send_news(bot, GROUP_CHAT_ID, sent_urls)
    except Exception as e:
        print(f"❗️ خطا در اجرای scheduled_job: {e}")

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❗️ توکن ربات یافت نشد. لطفاً متغیر BOT_TOKEN را در محیط تعریف کنید.")
        return

    app = ApplicationBuilder().token(token).build()

    async def run_scheduler():
        while True:
            await scheduled_job(app.bot)
            await asyncio.sleep(15)

    # اجرای زمان‌بندی موازی با polling ربات
    asyncio.create_task(run_scheduler())
    print("🚀 ربات در حال اجراست...")
    await app.run_polling()

# اجرای حلقه بدون استفاده از asyncio.run()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
