import os
from telegram import Bot
from telegram.constants import ParseMode

async def fetch_and_send_news(application):
    # گرفتن Bot از اپلیکیشن
    bot: Bot = application.bot

    # شناسه گروه یا کانال از متغیر محیطی یا به صورت مستقیم
    chat_id = int(os.getenv("CHAT_ID", "-1002514471809"))  # گروه سردبیری کافه شمس

    # پیام تستی
    message = "✅ تست fetch_and_send_news با موفقیت اجرا شد."

    # ارسال پیام
    await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
