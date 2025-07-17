import os
import sys
import logging
import threading
import asyncio
from flask import Flask, request, jsonify

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
from telegram import Update
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

# Port handling with fallback
PORT = int(os.getenv("PORT", "8443"))
WEBHOOK_URL = f"https://{HOST}/{BOT_TOKEN}"

# 4. ساخت اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# 5. Flask app for webhook
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    return jsonify({"status": "OK", "message": "Bot is running"}), 200

@flask_app.route('/')
def index():
    return jsonify({"status": "OK", "message": "Cafe Shams News Bot"}), 200

@flask_app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        if request.method == 'POST':
            update_data = request.get_json()
            if update_data:
                update = Update.de_json(update_data, app.bot)
                # Process update in background thread with proper async context
                def process_update():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        async def handle_update():
                            # Ensure app is initialized in this context
                            if not app.running:
                                await app.initialize()
                            await app.process_update(update)
                        
                        loop.run_until_complete(handle_update())
                        loop.close()
                    except Exception as e:
                        logging.error(f"Error processing update: {e}")
                
                thread = threading.Thread(target=process_update)
                thread.daemon = True
                thread.start()
        
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# 6. تعریف Job
async def news_job(ctx: ContextTypes.DEFAULT_TYPE):
    try:
        logging.info("Starting news job...")
        sent_urls = load_set("sent_urls.json")
        sent_hashes = load_set("sent_hashes.json")
        await fetch_and_send_news(ctx.bot, EDITORS_CHAT_ID, sent_urls, sent_hashes)
        logging.info("News job completed successfully")
    except Exception as e:
        logging.error(f"News job error: {e}")

# Job interval: 5 minutes
app.job_queue.run_repeating(news_job, interval=300, first=30)

# 7. Initialize webhook and start job queue
def initialize_bot():
    """Initialize bot webhook and start job queue"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def setup():
            # Initialize application
            await app.initialize()
            logging.info("Application initialized")
            
            # Set webhook
            await app.bot.set_webhook(WEBHOOK_URL)
            logging.info(f"Webhook set: {WEBHOOK_URL}")
            
            # Start job queue
            await app.job_queue.start()
            logging.info("Job queue started")
        
        loop.run_until_complete(setup())
        loop.close()
    except Exception as e:
        logging.error(f"Bot initialization error: {e}")

# 8. Main execution
if __name__ == "__main__":
    logging.info(f"Bot starting; EDITORS_CHAT_ID={EDITORS_CHAT_ID}, CHANNEL_ID={CHANNEL_ID}")
    logging.info(f"Using PORT: {PORT}")
    
    # Initialize bot
    initialize_bot()
    
    # Start Flask app
    flask_app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        threaded=True
    )
