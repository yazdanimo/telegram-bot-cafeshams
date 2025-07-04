import os
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

GROUP_CHAT_ID = -1000000000000  # عدد چت خودت رو جایگزین کن
sent_urls = set()

async def scheduled_job(bot):
    global sent_urls
    print("🔄 اجرای scheduled_job در حال انجام است...")
    try:
        sent_urls = await fetch_and_send_news(bot, GROUP_CHAT_ID, sent_urls)
    except Exception as e:
        print(f"❗️ خطا در اجرای scheduled_job: {e}")

async def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❗️ BOT_TOKEN تعریف نشده.")
        return

    app = ApplicationBuilder().token(token).build()

    async def scheduler():
        while True:
            await scheduled_job(app.bot)
            await asyncio.sleep(15)

    asyncio.create_task(scheduler())
    print("🚀 ربات آماده است.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()  # حلقه اجرا بدون بسته‌شدن

if __name__ == "__main__":
    try:
        asyncio.get_running_loop()
        # Railway یا Jupyter مانند: لوپ در حال اجراست
        asyncio.create_task(run_bot())
    except RuntimeError:
        # محیط‌های معمول: لوپ تازه بساز
        asyncio.run(run_bot())
