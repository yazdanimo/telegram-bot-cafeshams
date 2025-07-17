import os
import sys
import asyncio
import logging
import threading
import time
import re
import hashlib
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
sent_news = set()  # ذخیره خبرهای ارسال شده - reset شده

@flask_app.route('/clear-cache')
def clear_cache():
    """پاک کردن کش خبرهای ارسال شده"""
    global sent_news
    sent_news.clear()
    
    return jsonify({
        "status": "OK",
        "message": "News cache cleared - next news will use new format",
        "cache_size": len(sent_news)
    })

@flask_app.route('/')
def home():
    return jsonify({
        "status": "WORKING",
        "message": "Cafe Shams News Bot - Production Ready",
        "version": "v1.0-final",
        "auto_news": auto_news_running,
        "endpoints": ["/health", "/test", "/send", "/news", "/start-auto", "/stop-auto", "/stats", "/test-channel-access"]
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
    try:
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(fetch_news_async_with_report(bot))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

@flask_app.route('/start-auto')
def start_auto():
    """شروع خبرگیری خودکار"""
    global auto_news_running
    
    if auto_news_running:
        return jsonify({"status": "ALREADY_RUNNING", "message": "Auto news is already running"})
    
    auto_news_running = True
    
    # شروع thread خبرگیری خودکار (با اجرای فوری)
    auto_thread = threading.Thread(target=auto_news_worker, daemon=True)
    auto_thread.start()
    
    return jsonify({
        "status": "STARTED",
        "message": "Auto news started - immediate first run, then every 3 minutes",
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

@flask_app.route('/force-news')
def force_news():
    """اجبار ارسال خبر جدید با فرمت جدید"""
    global sent_news
    
    try:
        # پاک کردن کش
        sent_news.clear()
        
        # ارسال خبر جدید
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(fetch_news_async_with_report(bot))
        loop.close()
        
        return jsonify({
            "status": "SUCCESS",
            "message": "Cache cleared and fresh news sent with new format",
            "result": result
        })
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})
def stats():
    """آمار ربات"""
    return jsonify({
        "status": "OK",
        "total_sent": len(sent_news),
        "auto_running": auto_news_running,
        "editors_chat": EDITORS_CHAT_ID,
        "channel_id": CHANNEL_ID
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
                        # ارسال به کانال با HTML formatting
                        channel_msg = await bot.send_message(
                            chat_id=CHANNEL_ID,
                            text=message_text,
                            parse_mode='HTML',  # تغییر از Markdown به HTML
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

# حذف تابع قدیمی که دیگه استفاده نمیشه
# def fetch_and_send_news_sync() - حذف شده

# حذف تابع قدیمی که دیگه استفاده نمیشه  
# async def fetch_news_async() - حذف شده

def auto_news_worker():
    """Worker thread برای خبرگیری خودکار"""
    global auto_news_running
    
    logging.info("🤖 Auto news worker started")
    
    # اجرای فوری اولین دور بدون انتظار
    try:
        logging.info("⚡ Initial news cycle (immediate)")
        bot = Bot(token=BOT_TOKEN)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(fetch_news_async_with_report(bot))
        loop.close()
        
        if result["status"] == "SUCCESS":
            logging.info(f"✅ Initial news: {result['title']}")
        else:
            logging.info("ℹ️ Initial news: No new news found")
    except Exception as e:
        logging.error(f"Initial news error: {e}")
    
    # ادامه حلقه خبرگیری خودکار
    while auto_news_running:
        try:
            # انتظار 3 دقیقه
            for i in range(180):  # 180 seconds = 3 minutes
                if not auto_news_running:
                    break
                time.sleep(1)
            
            if not auto_news_running:
                break
                
            logging.info("⏰ Auto news cycle started")
            
            # اجرای خبرگیری
            bot = Bot(token=BOT_TOKEN)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(fetch_news_async_with_report(bot))
            loop.close()
            
            if result["status"] == "SUCCESS":
                logging.info(f"✅ Auto news: {result['title']}")
            else:
                logging.info("ℹ️ Auto news: No new news found")
                
        except Exception as e:
            logging.error(f"Auto news error: {e}")
            time.sleep(60)  # در صورت خطا، 1 دقیقه صبر
    
    logging.info("🛑 Auto news worker stopped")

async def fetch_news_async_with_report(bot):
    """جمع‌آوری اخبار با گزارش کامل - از همه منابع"""
    import feedparser
    
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
    
    # آمار برای گزارش
    stats = []
    total_news_sent = 0
    sent_news_list = []
    
    for source in sources:
        got = sent = err = 0
        
        try:
            logging.info(f"📡 بررسی {source['name']}")
            
            # دریافت RSS با timeout
            try:
                feed = feedparser.parse(source['url'])
                if not feed.entries:
                    logging.warning(f"⚠️ {source['name']}: هیچ خبری یافت نشد")
                    got = 0
                else:
                    got = len(feed.entries)
            except Exception as e:
                logging.error(f"❌ {source['name']}: خطا در RSS - {e}")
                err += 1
                stats.append({"src": source['name'], "got": got, "sent": sent, "err": err})
                continue
            
            # بررسی اخبار این منبع (حداکثر 3 خبر از هر منبع)
            for i, entry in enumerate(feed.entries[:3]):
                if got > 0:
                    title = entry.get('title', 'بدون عنوان')
                    link = entry.get('link', '')
                    
                    if title and link:
                        # بررسی تکراری نبودن
                        news_hash = hashlib.md5(f"{source['name']}{title}".encode()).hexdigest()
                        if news_hash not in sent_news:
                            # پردازش و ارسال خبر
                            try:
                                result = await process_and_send_news(bot, source, entry, news_hash)
                                if result:
                                    sent += 1
                                    total_news_sent += 1
                                    sent_news_list.append({
                                        "source": source['name'],
                                        "title": title[:50] + "..."
                                    })
                                    
                                    # فاصله بین ارسال اخبار (10 ثانیه)
                                    await asyncio.sleep(10)
                                    
                            except Exception as e:
                                logging.error(f"❌ خطا در پردازش خبر {source['name']}: {e}")
                                err += 1
                        else:
                            logging.info(f"🔄 {source['name']}: خبر تکراری - رد شد")
                
        except Exception as e:
            logging.error(f"❌ خطا در {source['name']}: {e}")
            err += 1
            
        stats.append({"src": source['name'], "got": got, "sent": sent, "err": err})
    
    # ارسال گزارش
    await send_report(bot, stats, total_news_sent, sent_news_list)
    
    if total_news_sent > 0:
        return {
            "status": "SUCCESS",
            "total_sent": total_news_sent,
            "news_list": sent_news_list,
            "total_sources": len(sources)
        }
    else:
        return {
            "status": "NO_NEWS", 
            "message": "هیچ خبر جدیدی در هیچ‌کدام از ۲۷ منبع یافت نشد",
            "total_sources_checked": len(sources)
        }

async def process_and_send_news(bot, source, entry, news_hash):
    """پردازش و ارسال یک خبر"""
    try:
        title = entry.get('title', 'بدون عنوان')
        link = entry.get('link', '')
        
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
        summary = re.sub(r'<[^>]+>', '', summary)
        summary = summary.strip()
        
        # محدود کردن طول خلاصه
        if len(summary) > 400:
            summary = summary[:400] + "..."
        elif len(summary) < 100:
            summary = title

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

        # فرمت پیام با styling زیبا و instant view
        message_text = f"""📰 **{source_name_en}**

**{title}**

{summary}

🔗 {link}

🆔 @cafeshamss     
کافه شمس ☕️🍪"""

        # ساخت دکمه
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ ارسال به کانال", callback_data=f"forward:{news_hash}")]
        ])
        
        # ارسال به گروه ادیتورها
        msg = await bot.send_message(
            chat_id=EDITORS_CHAT_ID,
            text=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown',
            disable_web_page_preview=False,
            disable_notification=False
        )
        
        # ذخیره در مجموعه ارسال شده
        sent_news.add(news_hash)
        
        logging.info(f"✅ خبر ارسال شد از {source['name']}: {title}")
        return True
        
    except Exception as e:
        logging.error(f"❌ خطا در ارسال خبر: {e}")
        return False

async def send_report(bot, stats, total_news_sent, sent_news_list):
    """ارسال گزارش جامع"""
    try:
        # محاسبه کل آمار
        total_sources = len(stats)
        total_got = sum(s["got"] for s in stats)
        total_sent = sum(s["sent"] for s in stats)
        total_err = sum(s["err"] for s in stats)
        
        # ساخت جدول گزارش
        lines = [
            "📊 News Collection Report",
            f"🔄 Total sources checked: {total_sources}",
            f"📰 Total news found: {total_got}",
            f"✅ Total sent: {total_sent}",
            f"❌ Total errors: {total_err}",
            "",
            "Source              Found  Sent  Err",
            "─────────────────── ─────  ────  ───"
        ]
        
        for r in stats:
            src_name = r["src"]
            # ترجمه نام منابع فارسی به انگلیسی برای گزارش
            src_name_en = {
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
            }.get(src_name, src_name)
            
            if len(src_name_en) > 18:
                src_name_en = src_name_en[:15] + "..."
            
            lines.append(f"{src_name_en:<19} {r['got']:>5}  {r['sent']:>4}  {r['err']:>3}")
        
        lines.append("")
        if total_news_sent > 0:
            lines.append(f"✅ {total_news_sent} news sent successfully")
        else:
            lines.append("ℹ️ No new news found in this cycle")
        
        lines.append("⏰ Next cycle in 3 minutes...")
        
        report = "<pre>" + "\n".join(lines) + "</pre>"
        
        # ارسال گزارش
        await bot.send_message(
            chat_id=EDITORS_CHAT_ID,
            text=report,
            parse_mode="HTML"
        )
        
        logging.info("📑 گزارش جامع ارسال شد")
        
    except Exception as e:
        logging.error(f"خطا در ارسال گزارش: {e}")

if __name__ == "__main__":
    logging.info(f"🚀 Cafe Shams News Bot starting on port {PORT}")
    
    # شروع خودکار خبرگیری بعد از deploy
    logging.info("🔄 Auto-starting news collection...")
    auto_news_running = True
    auto_thread = threading.Thread(target=auto_news_worker, daemon=True)
    auto_thread.start()
    
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)
