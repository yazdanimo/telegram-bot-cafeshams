import os
import sys
import asyncio
import logging
from flask import Flask, jsonify
from telegram import Bot

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN") or sys.exit("ERROR: BOT_TOKEN missing")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002514471809"))
PORT = int(os.getenv("PORT", "8443"))

# Flask app
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "WORKING",
        "message": "Emergency Simple Bot",
        "version": "minimal-v1",
        "endpoints": ["/health", "/test", "/send"]
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "OK", "port": PORT})

@flask_app.route('/test')
def test():
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Simple sync test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def check():
            me = await bot.get_me()
            return f"Bot: {me.first_name}"
        
        result = loop.run_until_complete(check())
        loop.close()
        
        return jsonify({"status": "OK", "bot": result})
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

@flask_app.route('/send')
def send():
    try:
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_msg():
            import time
            msg = await bot.send_message(
                chat_id=EDITORS_CHAT_ID,
                text=f"🟢 Emergency Bot Test\nزمان: {time.strftime('%H:%M:%S')}\n✅ کار می‌کند!"
            )
            return msg.message_id
        
        msg_id = loop.run_until_complete(send_msg())
        loop.close()
        
        return jsonify({
            "status": "SUCCESS", 
            "message_id": msg_id,
            "sent_to": EDITORS_CHAT_ID
        })
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

if __name__ == "__main__":
    logging.info(f"🚨 Emergency Bot starting on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)
