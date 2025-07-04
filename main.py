import os
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

# 📬 مقدار chat_id از محیط Railway یا مستقیم
GROUP_CHAT_ID = int(os.getenv("CHAT_ID", "-1000000000000"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
sent_urls = set()

async def scheduled_job(bot):
    global sent_urls
    print("🔄 اجرای scheduled_job...")
    try:
        sent_urls = await fetch_and_send_news(bot, GROUP_CHAT_ID, sent_urls)
    except Exception as e:
        print(f"❗️ خطا در scheduled_job: {e}")

async def run_bot():
    if not BOT_TOKEN:
        print("❗️ توکن ربات تعریف نشده.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # تست ارسال پیام برای بررسی chat_id
    try:
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text="✅ تست اتصال از کافه شمس ☕️🍪")
        print("📨 پیام تستی با موفقیت ارسال شد.")
    except Exception as e:
        print(f"🚫 خطا در ارسال تستی: {e}")

    # اجرای job هر ۶۰ ثانیه
    async def scheduler():
        while True:
            await scheduled_job(app.bot)
            await asyncio.sleep(60)

    # اجرای اپلیکیشن
    await app.initialize()
    await app.start()
    asyncio.create_task(scheduler())
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(run_bot())
        loop.run_forever()
