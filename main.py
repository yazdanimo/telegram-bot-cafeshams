# main.py
import os
import logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news
from utils import load_set

# setup logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

BOT_TOKEN       = os.getenv("BOT_TOKEN")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID"))
CHANNEL_ID      = int(os.getenv("CHANNEL_ID"))  # برای ارسال از handler

app = ApplicationBuilder().token(BOT_TOKEN).build()

# هندلر کال‌بک دکمهٔ ارسال به کانال
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# Job queue برای اجرای fetch_and_send_news هر 180 ثانیه
async def news_job(context):
    sent_urls   = load_set("sent_urls.json")
    sent_hashes = load_set("sent_hashes.json")
    await fetch_and_send_news(
        context.bot,
        EDITORS_CHAT_ID,
        sent_urls,
        sent_hashes
    )

app.job_queue.run_repeating(news_job, interval=180, first=0)

if __name__ == "__main__":
    PORT       = int(os.getenv("PORT", 8443))
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )
