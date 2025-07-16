# main.py

import os
import sys
import logging

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news
from utils import load_set

# تنظیم لاگینگ
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG
)

BOT_TOKEN = os.getenv("BOT_TOKEN") or sys.exit("ERROR: متغیر محیطی BOT_TOKEN تعریف نشده")

# گروه تایید خبر
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002685190359"))
# کانال نهایی
CHANNEL_ID      = int(os.getenv("CHANNEL_ID", str(EDITORS_CHAT_ID)))

# خودکار از Railway خوانده می‌شود
HOST = os.getenv("RAILWAY_STATIC_URL") or os.getenv("RAILWAY_URL") or os.getenv("SERVICE_URL")
if not HOST:
    sys.exit("ERROR: هیچ یک از RAILWAY_STATIC_URL یا RAILWAY_URL یا SERVICE_URL تعریف نشده")

PORT        = int(os.getenv("PORT", 8443))
WEBHOOK_URL = f"https://{HOST}/{BOT_TOKEN}"

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# برای اطمینان، لاگ شناسه‌ها
logging.info(f"🔑 EDITORS_CHAT_ID = {EDITORS_CHAT_ID}, CHANNEL_ID = {CHANNEL_ID}")
logging.info(f"🌐 Webhook URL = {WEBHOOK_URL}, PORT = {PORT}")

# تعریف تابع job به‌صورت async
async def news_job(context: ContextTypes.DEFAULT_TYPE):
    logging.info("🛰️ news_job started")
    sent_urls   = load_set("sent_urls.json")
    sent_hashes = load_set("sent_hashes.json")
    await fetch_and_send_news(
        context.bot,
        EDITORS_CHAT_ID,
        sent_urls,
        sent_hashes
    )

# ثبت دوره‌ای هر 180 ثانیه
app.job_queue.run_repeating(
    news_job,
    interval=180,
    first=0
)

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )
