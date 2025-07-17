import os
import sys
import asyncio
import logging
import threading
import time
import re
import hashlib
import json
from flask import Flask, jsonify, request
from telegram import Bot

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
sent_news_persistent = set()  # Set برای جلوگیری از تکرار بین گزارش‌ها

def load_sent_news():
    """بارگذاری خبرهای ارسال شده از فایل"""
    global sent_news_persistent
    try:
        if os.path.exists("sent_news.json"):
            with open("sent_news.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                sent_news_persistent = set(data)
                logging.info(f"📁 بارگذاری {len(sent_news_persistent)} خبر ارسال شده از فایل")
        else:
            sent_news_persistent = set()
    except Exception as e:
        logging.error(f"خطا در بارگذاری فایل sent_news: {e}")
        sent_news_persistent = set()

def save_sent_news():
    """ذخیره خبرهای ارسال شده در فایل"""
    try:
        with open("sent_news.json", "w", encoding="utf-8") as f:
            json.dump(list(sent_news_persistent), f, ensure_ascii=False, indent=2)
        logging.info(f"💾 ذخیره {len(sent_news_persistent)} خبر در فایل")
    except Exception as e:
        logging.error(f"خطا در ذخیره فایل sent_news: {e}")

@flask_app.route('/')
def home():
    return jsonify({
        "status": "WORKING",
        "message": "Cafe Shams News Bot - Production Ready",
        "version": "v2.0-translate",
        "auto_news": auto_news_running,
        "endpoints": ["/health", "/test", "/send", "/news", "/start-auto", "/stop-auto", "/stats", "/test-channel-access", "/clear-cache", "/force-news", "/test-translate"]
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
    global auto_news_running
    
    if auto_news_running:
        return jsonify({"status": "ALREADY_RUNNING", "message": "Auto news is already running"})
    
    auto_news_running = True
    
    auto_thread = threading.Thread(target=auto_news_worker, daemon=True)
    auto_thread.start()
    
    return jsonify({
        "status": "STARTED",
        "message": "Auto news started - immediate first run, then every 3 minutes",
        "interval": "180 seconds"
    })

@flask_app.route('/stop-auto')
def stop_auto():
    global auto_news_running
    auto_news_running = False
    
    return jsonify({
        "status": "STOPPED",
        "message": "Auto news stopped"
    })

@flask_app.route('/clear-cache')
def clear_cache():
    global sent_news_persistent
    sent_news_persistent.clear()
    save_sent_news()
    
    return jsonify({
        "status": "OK",
        "message": "News cache cleared permanently",
        "cache_size": len(sent_news_persistent)
    })

@flask_app.route('/force-news')
def force_news():
    global sent_news_persistent
    
    try:
        # فقط اگر کاربر بخواد کش پاک بشه
        # sent_news_persistent.clear()
        
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(fetch_news_async_with_report(bot))
        loop.close()
        
        return jsonify({
            "status": "SUCCESS",
            "message": "Fresh news sent (cache preserved)",
            "result": result
        })
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

@flask_app.route('/test-translate')
def test_translate():
    try:
        test_text = "Trump announces new policy on immigration"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def do_translate():
            result = await translate_text(test_text)
            return result
        
        result = loop.run_until_complete(do_translate())
        loop.close()
        
        return jsonify({
            "status": "OK",
            "original": test_text,
            "translated": result,
            "success": result is not None
        })
        
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

@flask_app.route('/stats')
def stats():
    return jsonify({
        "status": "OK",
        "total_sent": len(sent_news_persistent),
        "auto_running": auto_news_running,
        "editors_chat": EDITORS_CHAT_ID,
        "channel_id": CHANNEL_ID
    })

@flask_app.route('/test-channel-access')
def test_channel_access():
    try:
        bot = Bot(token=BOT_TOKEN)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def full_test():
            results = {}
            
            try:
                editors_chat = await bot.get_chat(EDITORS_CHAT_ID)
                results["editors_chat"] = {
                    "status": "OK",
                    "title": editors_chat.title,
                    "type": editors_chat.type
                }
            except Exception as e:
                results["editors_chat"] = {"status": "ERROR", "error": str(e)}
            
            try:
                channel_chat = await bot.get_chat(CHANNEL_ID)
                results["channel"] = {
                    "status": "OK", 
                    "title": channel_chat.title,
                    "type": channel_chat.type,
                    "username": getattr(channel_chat, 'username', None)
                }
                
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

def auto_news_worker():
    global auto_news_running
    
    logging.info("🤖 Auto news worker started")
    
    try:
        logging.info("⚡ Initial news cycle (immediate)")
        bot = Bot(token=BOT_TOKEN)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(fetch_news_async_with_report(bot))
        loop.close()
        
        if result["status"] == "SUCCESS":
            logging.info(f"✅ Initial news: sent {result.get('total_sent', 0)} news")
        else:
            logging.info("ℹ️ Initial news: No new news found")
    except Exception as e:
        logging.error(f"Initial news error: {e}")
    
    while auto_news_running:
        try:
            for i in range(180):
                if not auto_news_running:
                    break
                time.sleep(1)
            
            if not auto_news_running:
                break
                
            logging.info("⏰ Auto news cycle started")
            
            bot = Bot(token=BOT_TOKEN)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(fetch_news_async_with_report(bot))
            loop.close()
            
            if result["status"] == "SUCCESS":
                logging.info(f"✅ Auto news: sent {result.get('total_sent', 0)} news")
            else:
                logging.info("ℹ️ Auto news: No new news found")
                
        except Exception as e:
            logging.error(f"Auto news error: {e}")
            time.sleep(60)
    
    logging.info("🛑 Auto news worker stopped")

async def fetch_news_async_with_report(bot):
    import feedparser
    
    sources = [
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
    
    stats = []
    total_news_sent = 0
    sent_news_list = []
    
    for source in sources:
        got = sent = err = 0
        
        try:
            logging.info(f"📡 بررسی {source['name']}")
            
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
            
            for i, entry in enumerate(feed.entries[:3]):
                if got > 0:
                    title = entry.get('title', 'بدون عنوان')
                    link = entry.get('link', '')
                    
                    if title and link:
                        news_hash = hashlib.md5(f"{source['name']}{title}".encode()).hexdigest()
                        if news_hash not in sent_news_persistent:
                            try:
                                result = await process_and_send_news(bot, source, entry, news_hash)
                                if result:
                                    sent += 1
                                    total_news_sent += 1
                                    sent_news_list.append({
                                        "source": source['name'],
                                        "title": title[:50] + "..."
                                    })
                                    
                                    # ذخیره hash در فایل برای جلوگیری از تکرار
                                    sent_news_persistent.add(news_hash)
                                    save_sent_news()
                                    
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
    try:
        title = entry.get('title', 'بدون عنوان')
        link = entry.get('link', '')
        
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
        
        summary = re.sub(r'<[^>]+>', '', summary)
        summary = summary.strip()
        
        english_sources = [
            "Tehran Times", "Iran Front Page", "ABC News", "CNN", 
            "The Guardian", "Al Jazeera", "Foreign Affairs", "The Atlantic",
            "Brookings", "Carnegie", "Reuters", "AP News", "BBC World"
        ]
        
        if source['name'] in english_sources:
            try:
                logging.info(f"🔄 شروع ترجمه عنوان از {source['name']}: {title[:50]}...")
                title_fa = await translate_text(title)
                if title_fa and len(title_fa.strip()) > 5:
                    logging.info(f"✅ عنوان ترجمه شد: {title_fa[:50]}...")
                    title = title_fa
                else:
                    logging.warning(f"⚠️ ترجمه عنوان ناموفق، استفاده از fallback")
                    title = f"🌍 {title}"
            except Exception as e:
                logging.error(f"❌ خطا در ترجمه عنوان: {e}")
                title = f"🌍 {title}"
            
        # تشخیص زبان و ترجمه
        english_sources = [
            "Tehran Times", "Iran Front Page", "ABC News", "CNN", 
            "The Guardian", "Al Jazeera", "Foreign Affairs", "The Atlantic",
            "Brookings", "Carnegie", "Reuters", "AP News", "BBC World"
        ]
        
        if source['name'] in english_sources:
            try:
                logging.info(f"🔄 شروع ترجمه عنوان از {source['name']}: {title[:50]}...")
                title_fa = await translate_text(title)
                if title_fa and len(title_fa.strip()) > 5:
                    logging.info(f"✅ عنوان ترجمه شد: {title_fa[:50]}...")
                    title = title_fa
                else:
                    logging.warning(f"⚠️ ترجمه عنوان ناموفق، استفاده از fallback")
                    title = f"🌍 {title}"
            except Exception as e:
                logging.error(f"❌ خطا در ترجمه عنوان: {e}")
                title = f"🌍 {title}"
            
            if len(summary) > 50:
                try:
                    logging.info(f"🔄 شروع ترجمه خلاصه از {source['name']}: {summary[:30]}...")
                    summary_fa = await translate_text(summary)
                    if summary_fa and len(summary_fa.strip()) > 20:
                        logging.info(f"✅ خلاصه ترجمه شد: {summary_fa[:30]}...")
                        summary = summary_fa
                    else:
                        logging.warning(f"⚠️ ترجمه خلاصه ناموفق، استفاده از fallback")
                        summary = f"🌍 [English] {summary[:400]}..."
                except Exception as e:
                    logging.error(f"❌ خطا در ترجمه خلاصه: {e}")
                    summary = f"🌍 [English] {summary[:400]}..."
            else:
                summary = f"🌍 [English] {summary}"
        
        # تنظیم نهایی طول خلاصه
        if len(summary) > 800:
            summary = summary[:800] + "..."
        elif len(summary) < 100:
            summary = f"{title}\n\n[متن کامل در لینک زیر]"

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

        message_text = f"""📰 <b>{source_name_en}</b>

<b>{title}</b>

{summary}

🔗 <a href="{link}">مشاهده کامل خبر</a>

🆔 @cafeshamss     
کافه شمس ☕️🍪"""

        # حذف دکمه - ارسال مستقیم بدون دکمه
        msg = await bot.send_message(
            chat_id=EDITORS_CHAT_ID,
            text=message_text,
            parse_mode='HTML',
            disable_web_page_preview=False,
            disable_notification=False
        )
        
        # hash رو در فایل ذخیره نکن اینجا چون بالاتر ذخیره شده
        
        logging.info(f"✅ خبر ارسال شد از {source['name']}: {title}")
        return True
        
    except Exception as e:
        logging.error(f"❌ خطا در ارسال خبر: {e}")
        return False

async def translate_text(text):
    try:
        import aiohttp
        
        text_clean = text.strip()[:300]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.mymemory.translated.net/get"
                params = {
                    'q': text_clean,
                    'langpair': 'en|fa'
                }
                
                timeout = aiohttp.ClientTimeout(total=8)
                async with session.get(url, params=params, timeout=timeout) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result and 'responseData' in result:
                            translated = result['responseData']['translatedText']
                            if translated and len(translated) > 5 and translated != text_clean:
                                logging.info(f"✅ ترجمه موفق: {text_clean[:30]}... → {translated[:30]}...")
                                return translated
        except Exception as e:
            logging.warning(f"⚠️ خطا در ترجمه روش 1: {e}")
        
        logging.info(f"⚠️ ترجمه ناموفق، استفاده از fallback")
        return None
        
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return None

async def send_report(bot, stats, total_news_sent, sent_news_list):
    try:
        total_sources = len(stats)
        total_got = sum(s["got"] for s in stats)
        total_sent = sum(s["sent"] for s in stats)
        total_err = sum(s["err"] for s in stats)
        
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
    
    # بارگذاری خبرهای ارسال شده از فایل
    load_sent_news()
    
    # شروع خودکار خبرگیری بعد از deploy
    logging.info("🔄 Auto-starting news collection...")
    auto_news_running = True
    auto_thread = threading.Thread(target=auto_news_worker, daemon=True)
    auto_thread.start()
    
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)
