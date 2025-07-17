import aiohttp
import asyncio
import time
import hashlib
import logging
import feedparser
import re
from urllib.parse import urlparse, urlunparse, parse_qsl
from bs4 import BeautifulSoup
from translatepy import Translator
from utils import (
    load_sources,
    extract_full_content,
    summarize_fa,
    summarize_en,
    format_news,
    load_set,
    save_set,
    is_garbage,
    safe_send
)
from handlers import send_news_with_button

SEND_INTERVAL = 10  # فاصله بین ارسال اخبار
MAX_PER_CYCLE = 1   # فقط یک خبر در هر دور (تا تکرار نباشه)
FILES = {
    "urls": "sent_urls.json",
    "hashes": "sent_hashes.json",
    "bad": "bad_links.json"
}

translator = Translator()

def normalize_url(url: str) -> str:
    try:
        p = urlparse(url)
        qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
        return urlunparse((p.scheme, p.netloc, p.path, "", "&".join(f"{k}={v}" for k, v in qs), ""))
    except:
        return url

async def parse_rss(url: str):
    try:
        dp = await asyncio.wait_for(
            asyncio.to_thread(feedparser.parse, url),
            timeout=10
        )
        return dp.entries or []
    except asyncio.TimeoutError:
        logging.warning(f"RSS timeout: {url}")
        return []
    except Exception as e:
        logging.error(f"RSS parse error {url}: {e}")
        return []

async def fetch_html(session, url: str) -> str:
    try:
        async with session.get(url, timeout=5) as r:
            if r.status == 200:
                return await r.text()
    except asyncio.TimeoutError:
        logging.warning(f"HTML timeout: {url}")
    except Exception as e:
        logging.error(f"HTML fetch error {url}: {e}")
    return ""

async def safe_translate(text: str, target_lang: str = "fa") -> str:
    try:
        tr = await asyncio.wait_for(
            asyncio.to_thread(translator.translate, text, target_lang),
            timeout=10
        )
        return getattr(tr, "result", str(tr))
    except asyncio.TimeoutError:
        logging.warning("Translation timeout")
        return text
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text

async def fetch_and_send_news(bot, chat_id, sent_urls: set, sent_hashes: set):
    bad = load_set(FILES["bad"])
    stats = []
    new_urls = set()
    new_h = set()
    
    # پیام شروع دور جدید
    logging.info("🔄 شروع دور جدید جمع‌آوری اخبار...")
    
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=30)
    
    # متغیر برای کنترل ارسال فقط یک خبر در هر دور
    news_sent_in_cycle = False
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as sess:
        sources = load_sources()
        
        for src in sources:
            name, rss, fb, lang = src["name"], src["rss"], src["fallback"], src["lang"]
            got = sent = err = 0

            logging.info(f"📡 بررسی منبع: {name}")
            
            try:
                items = await parse_rss(rss)
                got = len(items)
                
                # اگر قبلاً در این دور خبری ارسال شده، فقط آمار جمع کن
                if news_sent_in_cycle:
                    logging.info(f"⏭️ رد شد: قبلاً در این دور خبر ارسال شده")
                    stats.append({"src": name, "got": got, "sent": 0, "err": 0})
                    continue
                
                for entry in items:
                    try:
                        link = entry.get("link", "").strip()
                        if not link:
                            continue
                            
                        u = normalize_url(link)
                        if not u or u in sent_urls | new_urls | bad:
                            continue

                        html = await fetch_html(sess, link)
                        if not html:
                            continue
                            
                        full = extract_full_content(html)
                        if is_garbage(full):
                            bad.add(u)
                            err += 1
                            continue

                        if lang == "en":
                            fa_text = await safe_translate(full, "fa")
                            summ = summarize_fa(fa_text)
                        else:
                            summ = summarize_fa(full)

                        if is_garbage(summ):
                            bad.add(u)
                            err += 1
                            continue

                        title = entry.get("title", "").strip() or name
                        text = format_news(name, title, summ, link)
                        h = hashlib.md5(text.encode()).hexdigest()
                        
                        if h in sent_hashes | new_h:
                            continue

                        logging.info(f"✅ ارسال خبر از {name}: {title}")
                        await send_news_with_button(bot, chat_id, text)
                        new_urls.add(u)
                        new_h.add(h)
                        sent += 1
                        news_sent_in_cycle = True  # علامت‌گذاری که خبر ارسال شد
                        
                        # خروج از حلقه چون فقط یک خبر در هر دور می‌خواهیم
                        break
                        
                    except Exception as e:
                        logging.error(f"خطا در پردازش خبر از {name}: {e}")
                        err += 1
                        
            except Exception as e:
                logging.error(f"خطا در پردازش منبع {name}: {e}")
                err += 1

            stats.append({"src": name, "got": got, "sent": sent, "err": err})
            
            # اگر خبری ارسال شد، از بقیه منابع صرف نظر کن
            if news_sent_in_cycle:
                break

    # به‌روزرسانی فایل‌های ردیابی
    sent_urls |= new_urls
    sent_hashes |= new_h
    save_set(sent_urls, FILES["urls"])
    save_set(sent_hashes, FILES["hashes"])
    save_set(bad, FILES["bad"])

    # تولید گزارش
    generate_report(bot, chat_id, stats, news_sent_in_cycle)

async def generate_report(bot, chat_id, stats, news_sent):
    """تولید و ارسال گزارش جامع"""
    
    # محاسبه کل آمار
    total_sources = len(stats)
    total_got = sum(s["got"] for s in stats)
    total_sent = sum(s["sent"] for s in stats)
    total_err = sum(s["err"] for s in stats)
    
    # ساخت جدول گزارش
    hdr = ["منبع", "دریافت", "ارسال", "خطا"]
    w = {"منبع": 20, "دریافت": 7, "ارسال": 6, "خطا": 4}
    
    lines = [
        "📊 گزارش دور جمع‌آوری اخبار",
        f"🔄 کل منابع بررسی شده: {total_sources}",
        f"📰 کل اخبار یافت شده: {total_got}",
        f"✅ تعداد ارسال شده: {total_sent}",
        f"❌ تعداد خطا: {total_err}",
        "",
        "  ".join(f"{h:<{w[h]}}" for h in hdr),
        "  ".join("-" * w[h] for h in hdr)
    ]
    
    for r in stats:
        src_name = r["src"]
        if len(src_name) > 18:
            src_name = src_name[:15] + "..."
            
        lines.append("  ".join([
            f"{src_name:<{w['منبع']}}",
            f"{r['got']:>{w['دریافت']}}",
            f"{r['sent']:>{w['ارسال']}}",
            f"{r['err']:>{w['خطا']}}"
        ]))
    
    lines.append("")
    if news_sent:
        lines.append("✅ در این دور یک خبر جدید ارسال شد")
    else:
        lines.append("ℹ️ در این دور خبر جدیدی یافت نشد")
    
    lines.append("⏰ دور بعدی تا 3 دقیقه دیگر...")
    
    report = "<pre>" + "\n".join(lines) + "</pre>"
    logging.info("📑 ارسال گزارش جامع")
    await safe_send(bot, chat_id, report, parse_mode="HTML")
