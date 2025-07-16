# main.py

import os
import sys
import logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news
from utils import load_set

# setup logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# required env vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    sys.exit("ERROR: BOT_TOKEN env var is not set")

# group chat where editors see items
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002685190359"))

# channel where approved items go
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002685190359"))

app = ApplicationBuilder().token(BOT_TOKEN).build()

# register callback handler for “forward_news”
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# periodic job: fetch & send to EDITORS_CHAT_ID
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
    PORT        = int(os.getenv("PORT", 8443))
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    if not WEBHOOK_URL:
        sys.exit("ERROR: WEBHOOK_URL env var is not set")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )
