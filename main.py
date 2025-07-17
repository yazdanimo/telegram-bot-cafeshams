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

# 4. ساخت اپلیکیشن با custom settings
app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(4).pool_timeout(30).connection_pool_size(8).read_timeout(30).write_timeout(30).build()
app.add_handler(CallbackQueryHandler(handle_forward_news, pattern="^forward_news$"))

# 5. Flask app for webhook
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return jsonify({
        "status": "OK", 
        "message": "Cafe Shams News Bot",
        "endpoints": {
            "/health": "Health check",
            "/debug": "Debug info", 
            "/test-news": "Manual news trigger",
            "/status": "Bot status"
        },
        "webhook": f"/{BOT_TOKEN}",
        "time": "4:11 AM"
    }), 200

@flask_app.route('/status')
def bot_status():
    """Bot status information"""
    import os
    return jsonify({
        "status": "RUNNING",
        "editors_chat": EDITORS_CHAT_ID,
        "channel_id": CHANNEL_ID,
        "webhook_url": WEBHOOK_URL,
        "files_exist": {
            "sources.json": os.path.exists("sources.json"),
            "utils.py": os.path.exists("utils.py"),
            "fetch_news.py": os.path.exists("fetch_news.py")
        }
    }), 200

@flask_app.route('/health')
def health_check():
    return jsonify({"status": "OK", "message": "Bot is running"}), 200

@flask_app.route('/debug')
def debug_info():
    """Debug endpoint to check file availability"""
    import os
    try:
        # Check current directory
        files = os.listdir('.')
        
        # Try to load sources
        try:
            from utils import load_sources
            sources = load_sources()
            sources_count = len(sources)
            sources_status = "OK"
        except Exception as e:
            sources_count = 0
            sources_status = str(e)
        
        return jsonify({
            "status": "DEBUG",
            "current_directory": os.getcwd(),
            "files_in_directory": files,
            "sources_count": sources_count,
            "sources_status": sources_status,
            "python_path": os.environ.get('PYTHONPATH', 'Not set')
        }), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@flask_app.route('/test-news')
def test_news():
    """Manual trigger for testing news fetch"""
    try:
        def run_news_job():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logging.info("Manual news job triggered")
                sent_urls = load_set("sent_urls.json")
                sent_hashes = load_set("sent_hashes.json")
                loop.run_until_complete(fetch_and_send_news(app.bot, EDITORS_CHAT_ID, sent_urls, sent_hashes))
            except Exception as e:
                logging.error(f"Manual news job error: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_news_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "OK", 
            "message": "News job triggered manually",
            "check": "Look at Railway logs for progress"
        }), 200
    except Exception as e:
        logging.error(f"Test news endpoint error: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500
def test_news():
    """Manual trigger for testing news fetch"""
    try:
        def run_news_job():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logging.info("Manual news job triggered")
                sent_urls = load_set("sent_urls.json")
                sent_hashes = load_set("sent_hashes.json")
                loop.run_until_complete(fetch_and_send_news(app.bot, EDITORS_CHAT_ID, sent_urls, sent_hashes))
            except Exception as e:
                logging.error(f"Manual news job error: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_news_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "OK", 
            "message": "News job triggered manually",
            "check": "Look at Railway logs for progress"
        }), 200
    except Exception as e:
        logging.error(f"Test news endpoint error: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500

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

# Job interval: هر 3 دقیقه (180 ثانیه) - شروع فوری
app.job_queue.run_repeating(news_job, interval=180, first=0)

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
