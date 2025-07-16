# main.py (نهایی)
import os, sys, logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news
from utils import load_set

logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

BOT_TOKEN = os.getenv("BOT_TOKEN") or sys.exit("ERROR: BOT_TOKEN نیست")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002685190359"))
CHANNEL_ID      = int(os.getenv("CHANNEL_ID", "-1002685190359"))

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# هر ۱۸۰ ثانیه اجرا می‌شه
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

WEBHOOK = os.getenv("WEBHOOK_URL")
if not WEBHOOK:
    sys.exit("ERROR: WEBHOOK_URL نیست")
PORT = int(os.getenv("PORT",8443))

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=WEBHOOK,
    allowed_updates=["message","callback_query"]
)
