import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news

# 📌 آیدی کانال یا چت تستی
GROUP_CHAT_ID = -1002514471809  # جایگزین کن با آیدی تست یا نهایی

# 🔐 توکن واقعی ربات
BOT_TOKEN = "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M"

sent_urls = set()

async def scheduled_job(bot):
    global sent_urls
    print("🔄 اجرای scheduled_job...")
    try:
        sent_urls = await fetch_and_send_news(bot, GROUP_CHAT_ID, sent_urls)
    except Exception as e:
        print(f"❗️ خطا در scheduled_job: {e}")

async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    try:
        await app.bot.send_message(chat_id=GROUP_CHAT_ID, text="✅ ربات کافه شمس آماده خبررسانی ☕️🍪")
        print("📨 پیام تستی با موفقیت ارسال شد.")
    except Exception as e:
        print(f"🚫 خطا در ارسال تستی: {e}")

    async def scheduler():
        while True:
            await scheduled_job(app.bot)
            await asyncio.sleep(60)

    await app.initialize()
    await app.start()
    asyncio.create_task(scheduler())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_bot())
