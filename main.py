import os
import sys
import logging

# 1. پیکربندی لاگینگ کلی
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)

# 2. کاهش verbosity برای httpx و apscheduler
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.INFO)

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes
from utils import load_set
from fetch_news import fetch_and_send_news
from handlers import handle_forward_news

# 3. خواندن ENVها
BOT_TOKEN       = os.getenv("BOT_TOKEN") or sys.exit("ERROR: BOT_TOKEN missing")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002514471809"))
CHANNEL_ID      = int(os.getenv("CHANNEL_ID", str(EDITORS_CHAT_ID)))

HOST = (
    os.getenv("RAILWAY_STATIC_URL")
    or os.getenv("RAILWAY_URL")
    or os.getenv("SERVICE_URL")
)
if not HOST:
    sys.exit("ERROR: HOST URL missing")

PORT        = int(os.getenv("PORT", 8443))
WEBHOOK_URL = f"https://{HOST}/{BOT_TOKEN}"

# 4. ساخت اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# 5. تعریف Job
async def news_job(ctx: ContextTypes.DEFAULT_TYPE):
    sent_urls   = load_set("sent_urls.json")
    sent_hashes = load_set("sent_hashes.json")
    await fetch_and_send_news(ctx.bot, EDITORS_CHAT_ID, sent_urls, sent_hashes)

app.job_queue.run_repeating(news_job, interval=180, first=0)

# 6. اجرای وب‌هوک
if __name__ == "__main__":
    logging.info(f"Bot starting; EDITORS_CHAT_ID={EDITORS_CHAT_ID}, CHANNEL_ID={CHANNEL_ID}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )
