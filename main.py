# main.py
import os
import sys
import logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news
from utils import load_set

logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    sys.exit("ERROR: BOT_TOKEN تنظیم نشده")

EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002685190359"))
CHANNEL_ID      = int(os.getenv("CHANNEL_ID",      "-1002685190359"))

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# JobQueue آماده است چون با [job-queue] نصب کردیم
app.job_queue.run_repeating(
    lambda ctx: fetch_and_send_news(
        ctx.bot,
        EDITORS_CHAT_ID,
        load_set("sent_urls.json"),
        load_set("sent_hashes.json")
    ),
    interval=180,
    first=0
)

if __name__ == "__main__":
    PORT       = int(os.getenv("PORT", 8443))
    WEBHOOK_URL= os.getenv("WEBHOOK_URL")
    if not WEBHOOK_URL:
        sys.exit("ERROR: WEBHOOK_URL تنظیم نشده")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )
