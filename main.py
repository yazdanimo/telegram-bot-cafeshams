# main.py

import os
import sys
import logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news
from utils import load_set

# —————— تنظیمات لاگ ——————
logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# —————— خواندن متغیرها ——————
BOT_TOKEN = os.getenv("BOT_TOKEN") or sys.exit("ERROR: متغیر محیطی BOT_TOKEN تعریف نشده")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002685190359"))
CHANNEL_ID      = int(os.getenv("CHANNEL_ID", EDITORS_CHAT_ID))

# Railway خودش آدرس سرویس را در یکی از این متغیرها می‌گذارد:
host = (
    os.getenv("RAILWAY_STATIC_URL")
    or os.getenv("RAILWAY_URL")
    or os.getenv("SERVICE_URL")
)
if not host:
    sys.exit("ERROR: هیچ یک از RAILWAY_STATIC_URL یا RAILWAY_URL یا SERVICE_URL تعریف نشده")

PORT = int(os.getenv("PORT", 8443))
WEBHOOK_URL = f"https://{host}/{BOT_TOKEN}"

# —————— ساخت اپلیکیشن ——————
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# —————— JobQueue: هر ۱۸۰ ثانیه اجرا می‌کند ——————
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

# —————— اجرای وبهوک ——————
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=WEBHOOK_URL,
    allowed_updates=["message", "callback_query"]
)
