# main.py

import os
import sys
import logging
import asyncio
import threading
import time

from flask import Flask, jsonify
from telegram import Bot

from fetch_news import fetch_and_send_news
from utils import load_set

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Environment variables
BOT_TOKEN       = os.getenv("BOT_TOKEN") or sys.exit("ERROR: BOT_TOKEN missing")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002514471809"))
CHANNEL_ID      = int(os.getenv("CHANNEL_ID", str(EDITORS_CHAT_ID)))
PORT            = int(os.getenv("PORT", "8443"))

# Telegram Bot instance
bot = Bot(token=BOT_TOKEN)

# Control flag for auto news
auto_news_running = False

def fetch_and_send_news_sync():
    """
    Wrapper to run async fetch_and_send_news in a new event loop.
    """
    sent_urls   = load_set("sent_urls.json")
    sent_hashes = load_set("sent_hashes.json")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            fetch_and_send_news(bot, EDITORS_CHAT_ID, sent_urls, sent_hashes)
        )
    finally:
        loop.close()

def auto_news_worker():
    """
    Background thread that fetches and sends news every 180 seconds.
    """
    while auto_news_running:
        logging.info("🔄 Auto news worker: fetching & sending news")
        try:
            fetch_and_send_news_sync()
        except Exception as e:
            logging.error(f"Error in auto_news_worker: {e}")
        time.sleep(180)


# Flask application
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "WORKING",
        "version": "v1.0",
        "auto_news": auto_news_running,
        "endpoints": [
            "/health",
            "/test",
            "/send",
            "/news",
            "/start-auto",
            "/stop-auto",
            "/stats"
        ]
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "OK", "auto_running": auto_news_running})

@flask_app.route('/test')
def test():
    try:
        me = bot.get_me()
        return jsonify({"status": "OK", "bot": me.first_name})
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

@flask_app.route('/send')
def send():
    """
    Send a test message to the editors chat.
    """
    try:
        msg = bot.send_message(
            chat_id=EDITORS_CHAT_ID,
            text=(
                "🟢 Test Message\n"
                f"زمان: {time.strftime('%H:%M:%S')}\n"
                "✅ کار می‌کند!"
            )
        )
        return jsonify({"status": "SUCCESS", "message_id": msg.message_id})
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

@flask_app.route('/news')
def news():
    """
    Manual trigger to fetch and send news once.
    """
    fetch_and_send_news_sync()
    return jsonify({"status": "SUCCESS", "message": "News sent manually"})

@flask_app.route('/start-auto')
def start_auto():
    """
    Start automatic news fetching every 3 minutes.
    """
    global auto_news_running
    if auto_news_running:
        return jsonify({"status": "ALREADY_RUNNING", "message": "Auto news already running"})
    auto_news_running = True
    threading.Thread(target=auto_news_worker, daemon=True).start()
    return jsonify({"status": "STARTED", "message": "Auto news started", "interval": "180 seconds"})

@flask_app.route('/stop-auto')
def stop_auto():
    """
    Stop the automatic news fetching thread.
    """
    global auto_news_running
    auto_news_running = False
    return jsonify({"status": "STOPPED", "message": "Auto news stopped"})

@flask_app.route('/stats')
def stats():
    """
    Return simple stats on how many URLs and hashes have been sent.
    """
    sent_urls   = load_set("sent_urls.json")
    sent_hashes = load_set("sent_hashes.json")
    return jsonify({
        "status": "OK",
        "sent_urls_count":   len(sent_urls),
        "sent_hashes_count": len(sent_hashes)
    })


if __name__ == '__main__':
    logging.info(f"📡 Starting Flask server on port {PORT}")
    flask_app.run(host='0.0.0.0', port=PORT)
