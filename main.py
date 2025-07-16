# main.py

import os
import sys
import logging
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news
from utils import load_set

# ————————— تنظیمات لاگ —————————
logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ————————— خواندن متغیرها —————————
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    sys.exit("ERROR: متغیر محیطی BOT_TOKEN تنظیم نشده")

# اینجا دامنه‌ی ریلیتو بزار:
#   Value = telegram-bot-cafeshams-production.up.railway.app
HOST = os.getenv("HOST")
if not HOST:
    sys.exit("ERROR: متغیر محیطی HOST تنظیم نشده (مثال: telegram-bot-cafeshams-production.up.railway.app)")

# شناسه گروه سردبیری و کانال
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002685190359"))
CHANNEL_ID      = int(os.getenv("CHANNEL_ID",      "-1002685190359"))

# ————————— ساخت اپلیکیشن —————————
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# ————————— JobQueue برای هر ۱۸۰ ثانیه —————————
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

# ————————— وب‌هوک —————————
PORT = int(os.getenv("PORT", 8443))
# ساخت URL کامل وب‌هوک با پروتکل و توکن
WEBHOOK_URL = f"https://{HOST}/{BOT_TOKEN}"

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=WEBHOOK_URL,
    allowed_updates=["message", "callback_query"]
)
