import os
import sys
import logging
from flask import Flask, request

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
BOT_TOKEN = os.getenv("BOT_TOKEN") or sys.exit("ERROR: BOT_TOKEN missing")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002514471809"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", str(EDITORS_CHAT_ID)))

# Railway URL handling
HOST = (
    os.getenv("RAILWAY_STATIC_URL", "").replace("https://", "")
    or os.getenv("RAILWAY_URL", "").replace("https://", "")
    or os.getenv("SERVICE_URL", "").replace("https://", "")
)

if not HOST:
    sys.exit("ERROR: HOST URL missing")

PORT = int(os.getenv("PORT", 8443))
WEBHOOK_URL = f"https://{HOST}/{BOT_TOKEN}"

# 4. Flask app for health check
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    return "OK", 200

@flask_app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = request.get_json()
        if update:
            # Process update asynchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(app.process_update(update))
            loop.close()
    return "OK", 200

# 5. ساخت اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# 6. تعریف Job
async def news_job(ctx: ContextTypes.DEFAULT_TYPE):
    try:
        sent_urls = load_set("sent_urls.json")
        sent_hashes = load_set("sent_hashes.json")
        await fetch_and_send_news(ctx.bot, EDITORS_CHAT_ID, sent_urls, sent_hashes)
    except Exception as e:
        logging.error(f"News job error: {e}")

# Job interval increased to 5 minutes
app.job_queue.run_repeating(news_job, interval=300, first=10)

# 7. اجرای وب‌هوک
if __name__ == "__main__":
    logging.info(f"Bot starting; EDITORS_CHAT_ID={EDITORS_CHAT_ID}, CHANNEL_ID={CHANNEL_ID}")
    logging.info(f"Webhook URL: {WEBHOOK_URL}")
    
    # Set webhook
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(app.bot.set_webhook(WEBHOOK_URL))
    loop.close()
    
    # Start Flask app
    flask_app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
