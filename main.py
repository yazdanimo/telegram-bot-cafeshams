import os
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

# 🔐 مقدار chat ID مقصد (مثلاً: -1001234567890 یا آی‌دی عددی شخصی‌ات برای تست)
GROUP_CHAT_ID = int(os.getenv("CHAT_ID", "-1000000000000"))

# 🔐 توکن ربات از محیط Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")

# لیست لینک‌هایی که ارسال شدن (در حالت واقعی می‌تونه در فایل ذخیره بشه)
sent_urls = set()

async def scheduled_job(bot):
    global sent_urls
    print("🔄 اجرای scheduled_job در حال انجام است...")
    try:
        sent_urls = await fetch_and_send_news(bot, GROUP_CHAT_ID, sent_urls)
    except Exception as e:
        print(f"❗️ خطا در اجرای scheduled_job: {e}")

async def run_bot():
    if not BOT_TOKEN:
        print("❗️ BOT_TOKEN تنظیم نشده.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # تست اولیه برای اتصال به چت
    try:
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text="✅ تست اتصال از کافه شمس ☕️🍪")
        print("📬 پیام تستی ارسال شد.")
    except Exception as e:
        print(f"🚫 خطا در ارسال پیام تستی: {e}")

    # اجرای job زمان‌بندی‌شده
    async def scheduler():
        while True:
            await scheduled_job(app.bot)
            await asyncio.sleep(60)  # هر ۶۰ ثانیه اجرا بشه

    asyncio.create_task(scheduler())

    # اجرای اصلی اپلیکیشن
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(run_bot())
        loop.run_forever()
