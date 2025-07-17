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
        "message": "Cafe Shams News Bot v2",
        "version": "news-ready",
        "endpoints": ["/health", "/test", "/send", "/news"]
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "OK", "port": PORT})

@flask_app.route('/test')
def test():
    try:
        bot = Bot(token=BOT_TOKEN)
        
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

@flask_app.route('/news')
def news():
    """جمع‌آوری و ارسال اخبار"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def fetch_news():
            import feedparser
            import time
            from urllib.parse import urlparse
            
            # منابع خبری ساده
            sources = [
                {"name": "مهر", "url": "https://www.mehrnews.com/rss"},
                {"name": "فارس", "url": "https://www.farsnews.ir/rss"},
                {"name": "ایرنا", "url": "https://www.irna.ir/rss"}
            ]
            
            news_found = False
            
            for source in sources:
                try:
                    logging.info(f"📡 بررسی {source['name']}")
                    
                    # دریافت RSS
                    feed = feedparser.parse(source['url'])
                    
                    if feed.entries:
                        # اولین خبر
                        entry = feed.entries[0]
                        title = entry.get('title', 'بدون عنوان')
                        link = entry.get('link', '')
                        
                        # فرمت پیام
                        message_text = f"📰 {source['name']}\n\n🔸 {title}\n\n🔗 {link}\n\n⏰ {time.strftime('%H:%M:%S')}"
                        
                        # ارسال به گروه
                        msg = await bot.send_message(
                            chat_id=EDITORS_CHAT_ID,
                            text=message_text
                        )
                        
                        news_found = True
                        return {
                            "source": source['name'],
                            "title": title,
                            "message_id": msg.message_id,
                            "link": link
                        }
                        
                except Exception as e:
                    logging.error(f"خطا در {source['name']}: {e}")
                    continue
            
            if not news_found:
                return {"error": "هیچ خبری یافت نشد"}
        
        result = loop.run_until_complete(fetch_news())
        loop.close()
        
        return jsonify({
            "status": "SUCCESS" if "error" not in result else "NO_NEWS",
            "result": result
        })
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

if __name__ == "__main__":
    logging.info(f"🚀 News Bot starting on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)
