import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

# 🔐 مقدار chat ID ثابت برای تست خصوصی (آیدی خودت)
GROUP_CHAT_ID = 53266006

# 🔐 توکن ربات (به صورت مستقیم وارد کن یا از محیط بخون)
BOT_TOKEN = "توکن_ربات_تو_اینجا"

# مجموعه لینک‌های ارسال‌شده
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
        print("❗️ BOT_TOKEN تعریف نشده.")
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

    await app.initialize()
    await app.start()
    asyncio.create_task(scheduler())
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(run_bot())
        loop.run_forever()
