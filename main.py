import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

# 🔐 توکن واقعی ربات از BotFather
BOT_TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"

# 🆔 آیدی چت تستی (خودت یا گروه آزمایشی)
GROUP_CHAT_ID = 53266006  # آیدی خودت برای تست

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

    # تست ارسال پیام اولیه
    try:
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text="✅ تست اتصال از کافه شمس ☕️🍪")
        print("📨 پیام تستی با موفقیت ارسال شد.")
    except Exception as e:
        print(f"🚫 خطا در ارسال تستی: {e}")

    # اجرای job زمان‌بندی‌شده
    async def scheduler():
        while True:
            await scheduled_job(app.bot)
            await asyncio.sleep(60)  # اجرا هر ۶۰ ثانیه

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
