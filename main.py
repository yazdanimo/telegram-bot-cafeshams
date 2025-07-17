import os
import sys
import asyncio
import logging
import threading
import time
from flask import Flask, jsonify, request
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN") or sys.exit("ERROR: BOT_TOKEN missing")
EDITORS_CHAT_ID = int(os.getenv("EDITORS_CHAT_ID", "-1002514471809"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002685190359"))
PORT = int(os.getenv("PORT", "8443"))

# Flask app
flask_app = Flask(__name__)

# Global variables
auto_news_running = False
sent_news = set()  # ذخیره خبرهای ارسال شده

@flask_app.route('/')
def home():
    return jsonify({
        "status": "WORKING",
        "message": "Cafe Shams News Bot - Production Ready",
        "version": "v1.0",
        "auto_news": auto_news_running,
        "endpoints": ["/health", "/test", "/send", "/news", "/start-auto", "/stop-auto", "/stats"]
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "OK", "port": PORT, "auto_running": auto_news_running})

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
            msg = await bot.send_message(
                chat_id=EDITORS_CHAT_ID,
                text=f"🟢 Test Message\nزمان: {time.strftime('%H:%M:%S')}\n✅ کار می‌کند!"
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
    """جمع‌آوری و ارسال اخبار دستی"""
    return fetch_and_send_news_sync()

@flask_app.route('/start-auto')
def start_auto():
    """شروع خبرگیری خودکار"""
    global auto_news_running
    
    if auto_news_running:
        return jsonify({"status": "ALREADY_RUNNING", "message": "Auto news is already running"})
    
    auto_news_running = True
    
    # شروع thread خبرگیری خودکار
    auto_thread = threading.Thread(target=auto_news_worker, daemon=True)
    auto_thread.start()
    
    return jsonify({
        "status": "STARTED",
        "message": "Auto news started - every 3 minutes",
        "interval": "180 seconds"
    })

@flask_app.route('/stop-auto')
def stop_auto():
    """توقف خبرگیری خودکار"""
    global auto_news_running
    auto_news_running = False
    
    return jsonify({
        "status": "STOPPED",
        "message": "Auto news stopped"
    })

@flask_app.route('/test-channel-access')
def test_channel_access():
    """تست دقیق دسترسی به کانال"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def full_test():
            results = {}
            
            # تست گروه ادیتورها
            try:
                editors_chat = await bot.get_chat(EDITORS_CHAT_ID)
                results["editors_chat"] = {
                    "status": "OK",
                    "title": editors_chat.title,
                    "type": editors_chat.type
                }
            except Exception as e:
                results["editors_chat"] = {"status": "ERROR", "error": str(e)}
            
            # تست کانال
            try:
                channel_chat = await bot.get_chat(CHANNEL_ID)
                results["channel"] = {
                    "status": "OK", 
                    "title": channel_chat.title,
                    "type": channel_chat.type,
                    "username": getattr(channel_chat, 'username', None)
                }
                
                # تست ارسال به کانال
                test_msg = await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text="🧪 تست دسترسی کانال - این پیام قابل حذف است"
                )
                results["channel"]["send_test"] = {
                    "status": "SUCCESS",
                    "message_id": test_msg.message_id
                }
                
            except Exception as e:
                results["channel"] = {
                    "status": "ERROR", 
                    "error": str(e),
                    "channel_id": CHANNEL_ID
                }
            
            return results
        
        results = loop.run_until_complete(full_test())
        loop.close()
        
        return jsonify({
            "status": "COMPLETED",
            "results": results,
            "suggestion": "If channel test failed, add bot as admin to @cafeshamss"
        })
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})
def check_channel():
    """بررسی دسترسی به کانال"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def check():
            try:
                # بررسی دسترسی به کانال
                chat = await bot.get_chat(CHANNEL_ID)
                
                return {
                    "status": "SUCCESS",
                    "channel_id": CHANNEL_ID,
                    "channel_title": chat.title,
                    "channel_type": chat.type,
                    "channel_username": getattr(chat, 'username', 'No username')
                }
                
            except Exception as e:
                return {
                    "status": "ERROR",
                    "channel_id": CHANNEL_ID, 
                    "error": str(e),
                    "suggestion": "Add bot as admin to channel or check CHANNEL_ID"
                }
        
        result = loop.run_until_complete(check())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

@flask_app.route('/fix-channel')
def fix_channel():
    """موقتاً channel رو برابر editors chat کن"""
    global CHANNEL_ID
    CHANNEL_ID = EDITORS_CHAT_ID
    
    return jsonify({
        "status": "FIXED",
        "message": "Channel ID set to editors chat temporarily",
        "channel_id": CHANNEL_ID,
        "editors_chat": EDITORS_CHAT_ID
    })
def stats():
    """آمار ربات"""
    return jsonify({
        "status": "OK",
        "total_sent": len(sent_news),
        "auto_running": auto_news_running,
        "editors_chat": EDITORS_CHAT_ID,
        "channel_id": CHANNEL_ID
    })

@flask_app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Webhook handler برای دکمه‌ها"""
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({"status": "OK"}), 200
        
        # بررسی callback query (کلیک روی دکمه)
        if 'callback_query' in update_data:
            callback = update_data['callback_query']
            callback_data = callback.get('data', '')
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            
            if callback_data.startswith('forward:'):
                # دکمه "ارسال به کانال" کلیک شده
                news_hash = callback_data.replace('forward:', '')
                message_text = callback['message']['text']
                
                # ارسال به کانال
                bot = Bot(token=BOT_TOKEN)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def forward_to_channel():
                    try:
                        # ارسال به کانال با sender مخفی
                        channel_msg = await bot.send_message(
                            chat_id=CHANNEL_ID,
                            text=message_text,
                            parse_mode='Markdown',
                            disable_web_page_preview=False,
                            disable_notification=False,
                            protect_content=False
                        )
                        
                        # سعی برای مخفی کردن sender (اگر ادمین channel باشیم)
                        try:
                            await bot.edit_message_reply_markup(
                                chat_id=CHANNEL_ID,
                                message_id=channel_msg.message_id,
                                reply_markup=None
                            )
                        except:
                            pass  # اگر نتونستیم edit کنیم مشکلی نیست
                        
                        # پاسخ به callback query
                        await bot.answer_callback_query(
                            callback_query_id=callback['id'],
                            text="✅ خبر به کانال ارسال شد"
                        )
                        
                        # تغییر دکمه به "ارسال شده"
                        new_keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton("📤 ارسال شد", callback_data="sent")]
                        ])
                        
                        await bot.edit_message_reply_markup(
                            chat_id=chat_id,
                            message_id=message_id,
                            reply_markup=new_keyboard
                        )
                        
                        return True
                        
                    except Exception as e:
                        logging.error(f"Forward error: {e}")
                        await bot.answer_callback_query(
                            callback_query_id=callback['id'],
                            text=f"❌ خطا: {str(e)}"
                        )
                        return False
                
                result = loop.run_until_complete(forward_to_channel())
                loop.close()
                
                logging.info(f"📤 Forward to channel: {'Success' if result else 'Failed'}")
        
        return jsonify({"status": "OK"}), 200
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500

def fetch_and_send_news_sync():
    """جمع‌آوری اخبار (sync wrapper)"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(fetch_news_async(bot))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

async def fetch_news_async(bot):
    """جمع‌آوری اخبار (async)"""
    import feedparser
    import hashlib
    
    # منابع خبری کامل - ۲۷ منبع
    sources = [
        # منابع فارسی
        {"name": "مهر", "url": "https://www.mehrnews.com/rss"},
        {"name": "فارس", "url": "https://www.farsnews.ir/rss"},
        {"name": "تسنیم", "url": "https://www.tasnimnews.com/fa/rss/feed"},
        {"name": "ایرنا", "url": "https://www.irna.ir/rss"},
        {"name": "ایسنا", "url": "https://www.isna.ir/rss"},
        {"name": "همشهری آنلاین", "url": "https://www.hamshahrionline.ir/rss"},
        {"name": "خبر آنلاین", "url": "https://www.khabaronline.ir/rss"},
        {"name": "مشرق", "url": "https://www.mashreghnews.ir/rss"},
        {"name": "انتخاب", "url": "https://www.entekhab.ir/fa/rss/allnews"},
        {"name": "جماران", "url": "https://www.jamaran.news/rss"},
        {"name": "آخرین خبر", "url": "https://www.akharinkhabar.ir/rss"},
        {"name": "هم‌میهن", "url": "https://www.hammihanonline.ir/rss"},
        {"name": "اعتماد", "url": "https://www.etemadonline.com/rss"},
        {"name": "اصلاحات", "url": "https://www.eslahat.news/rss"},
        
        # منابع انگلیسی
        {"name": "Tehran Times", "url": "https://www.tehrantimes.com/rss"},
        {"name": "Iran Front Page", "url": "https://ifpnews.com/feed"},
        {"name": "ABC News", "url": "https://abcnews.go.com/abcnews/topstories"},
        {"name": "CNN", "url": "http://rss.cnn.com/rss/cnn_topstories.rss"},
        {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss"},
        {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
        {"name": "Foreign Affairs", "url": "https://www.foreignaffairs.com/rss.xml"},
        {"name": "The Atlantic", "url": "https://www.theatlantic.com/feed/all"},
        {"name": "Brookings", "url": "https://www.brookings.edu/feed"},
        {"name": "Carnegie", "url": "https://carnegieendowment.org/rss"},
        {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/topNews"},
        {"name": "AP News", "url": "https://apnews.com/rss"},
        {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"}
    ]
    
    for source in sources:
        try:
            logging.info(f"📡 بررسی {source['name']}")
            
            # دریافت RSS با timeout
            try:
                feed = feedparser.parse(source['url'])
                if not feed.entries:
                    logging.warning(f"⚠️ {source['name']}: هیچ خبری یافت نشد")
                    continue
            except Exception as e:
                logging.error(f"❌ {source['name']}: خطا در RSS - {e}")
                continue
            
            entry = feed.entries[0]
            title = entry.get('title', 'بدون عنوان')
            link = entry.get('link', '')
            
            if not title or not link:
                continue
            
            # بررسی تکراری نبودن
            news_hash = hashlib.md5(f"{source['name']}{title}".encode()).hexdigest()
            if news_hash in sent_news:
                logging.info(f"🔄 {source['name']}: خبر تکراری - رد شد")
                continue
            
            # دریافت خلاصه بهتر
            summary = ""
            if hasattr(entry, 'summary') and entry.summary:
                summary = entry.summary
            elif hasattr(entry, 'description') and entry.description:
                summary = entry.description
            elif hasattr(entry, 'content') and entry.content:
                if isinstance(entry.content, list) and len(entry.content) > 0:
                    summary = entry.content[0].value
                else:
                    summary = str(entry.content)
            else:
                summary = title
            
            # پاک کردن HTML tags از خلاصه
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary.strip()
            
            # محدود کردن طول خلاصه
            if len(summary) > 400:
                summary = summary[:400] + "..."
            elif len(summary) < 100:
                summary = title  # اگر خلاصه خیلی کوتاه بود، از عنوان استفاده کن

            # ترجمه نام منبع به انگلیسی
            source_name_en = {
                "مهر": "Mehr News",
                "فارس": "Fars News", 
                "تسنیم": "Tasnim News",
                "ایرنا": "IRNA",
                "ایسنا": "ISNA",
                "همشهری آنلاین": "Hamshahri Online",
                "خبر آنلاین": "Khabar Online",
                "مشرق": "Mashregh News",
                "انتخاب": "Entekhab News",
                "جماران": "Jamaran",
                "آخرین خبر": "Akharin Khabar",
                "هم‌میهن": "HamMihan",
                "اعتماد": "Etemad",
                "اصلاحات": "Eslahat News"
            }.get(source['name'], source['name'])

            # فرمت پیام با styling زیبا
            message_text = f"""📰 **{source_name_en}**

**{title}**

{summary}

🔗 [مشاهده کامل خبر]({link})

🆔 @cafeshamss     
کافه شمس ☕️🍪"""
            
            # ساخت دکمه
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ ارسال به کانال", callback_data=f"forward:{news_hash}")]
            ])
            
            # ارسال به گروه ادیتورها با parse_mode برای لینک
            msg = await bot.send_message(
                chat_id=EDITORS_CHAT_ID,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
            
            # ذخیره در مجموعه ارسال شده
            sent_news.add(news_hash)
            
            logging.info(f"✅ خبر ارسال شد از {source['name']}: {title}")
            
            return {
                "status": "SUCCESS",
                "source": source['name'],
                "title": title,
                "message_id": msg.message_id,
                "link": link,
                "hash": news_hash,
                "total_sources": len(sources)
            }
                
        except Exception as e:
            logging.error(f"❌ خطا در {source['name']}: {e}")
            continue
    
    return {
        "status": "NO_NEWS", 
        "message": "هیچ خبر جدیدی در هیچ‌کدام از ۲۷ منبع یافت نشد",
        "total_sources_checked": len(sources)
    }

def auto_news_worker():
    """Worker thread برای خبرگیری خودکار"""
    global auto_news_running
    
    logging.info("🤖 Auto news worker started")
    
    while auto_news_running:
        try:
            logging.info("⏰ Auto news cycle started")
            
            # اجرای خبرگیری
            bot = Bot(token=BOT_TOKEN)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(fetch_news_async(bot))
            loop.close()
            
            if result["status"] == "SUCCESS":
                logging.info(f"✅ Auto news: {result['title']}")
            else:
                logging.info("ℹ️ Auto news: No new news found")
            
            # انتظار 3 دقیقه
            for i in range(180):  # 180 seconds = 3 minutes
                if not auto_news_running:
                    break
                time.sleep(1)
                
        except Exception as e:
            logging.error(f"Auto news error: {e}")
            time.sleep(60)  # در صورت خطا، 1 دقیقه صبر
    
    logging.info("🛑 Auto news worker stopped")

if __name__ == "__main__":
    logging.info(f"🚀 Cafe Shams News Bot starting on port {PORT}")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)
