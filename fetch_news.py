# File: fetch_news.py — نسخهٔ نهایی مرتب و بدون خطای نحوی

import aiohttp
import asyncio
import json
import time
import hashlib
import feedparser
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qsl
from utils import load_sources, extract_full_content, summarize_text, format_news

# مسیر فایل‌های وضعیت و گزارش
SEND_INTERVAL      = 3
LAST_SEND          = 0
SENT_URLS_FILE     = "sent_urls.json"
SENT_HASHES_FILE   = "sent_hashes.json"
BAD_LINKS_FILE     = "bad_links.json"
SKIPPED_LOG_FILE   = "skipped_items.json"
GARBAGE_NEWS_FILE  = "garbage_news.json"

def load_set(path):
    """
    تلاش برای بارگذاری یک لیست از فایل و تبدیل آن به set.
    در صورت خطا، مجموعهٔ خالی برمی‌گرداند.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except Exception:
        return set()

def save_set(data, path):
    """
    ذخیرهٔ یک set به صورت لیست در فایل JSON.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

def normalize_url(url):
    """
    حذف پارامترهای UTM و نرمال‌سازی URL.
    """
    p = urlparse(url)
    qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    query = "&".join(f"{k}={v}" for k, v in qs)
    return urlunparse((p.scheme, p.netloc, p.path, "", query, ""))

def is_garbage(text):
    """
    فیلتر محتوای بی‌کیفیت بر اساس طول،
    نسبت نویسه‌های فارسی، تکرار کاراکتر،
    و نشانه‌های غیرمعمول.
    """
    text = text.strip()
    if len(text) < 60:
        return True

    persian = re.findall(r'[\u0600-\u06FF]', text)
    if len(persian) / max(len(text), 1) < 0.4:
        return True

    if re.search(r'(.)\1{5,}', text):
        return True

    # تعداد رشته‌های لاتین طولانی
    latin_words = re.findall(r'[A-Za-z]{4,}', text)
    if len(latin_words) > 5 and len(persian) < 50:
        return True

    # کلمات معمول صفحات فرم یا ثبت‌نام
    for kw in ["ثبت نام", "login", "register", "signup"]:
        if kw in text:
            return True

    return False

def log_garbage(source, link, title, content):
    """
    ذخیرهٔ موارد محتوای خراب برای بازبینی.
    """
    try:
        with open(GARBAGE_NEWS_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        items = []

    items.append({
        "source": source,
        "link": link,
        "title": title,
        "content": content[:300]
    })
    with open(GARBAGE_NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def log_skipped(source, url, reason, title=None):
    """
    ذخیرهٔ موارد ردشده (تکراری، خراب، خطا) برای گزارش.
    """
    try:
        with open(SKIPPED_LOG_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        items = []

    items.append({
        "source": source,
        "url": url,
        "title": title,
        "reason": reason
    })
    with open(SKIPPED_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

async def safe_send(bot, chat_id, text, **kwargs):
    """
    ارسال پیام با رعایت فاصلهٔ زمانی بین دو ارسال.
    """
    global LAST_SEND
    elapsed = time.time() - LAST_SEND
    if elapsed < SEND_INTERVAL:
        await asyncio.sleep(SEND_INTERVAL - elapsed)
    try:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        print("⚠️ خطا در ارسال پیام:", e)
    finally:
        LAST_SEND = time.time()

async def parse_rss_async(url):
    """
    خواندن RSS به صورت async با timeout.
    """
    try:
        dp = await asyncio.wait_for(
            asyncio.to_thread(feedparser.parse, url),
            timeout=10
        )
        return dp.entries or []
    except Exception as e:
        print(f"⚠️ خطا در خواندن RSS {url}:", e)
        return []

async def fetch_html(session, url):
    """
    دریافت HTML یک صفحه با بررسی کد وضعیت HTTP.
    """
    async with session.get(url) as res:
        if res.status != 200:
            raise Exception(f"HTTP {res.status}")
        return await res.text()

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    """
    تابع اصلی: دریافت اخبار از منابع RSS،
    فیلتر و استخراج، مدیریت fallback،
    ارسال پیام‌ها و گزارش نهایی.
    """
    bad_links  = load_set(BAD_LINKS_FILE)
    stats      = []
    sent_now   = set()
    hashes_now = set()

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=20)
    ) as session:
        for src in load_sources():
            name   = src.get("name")
            rss    = src.get("rss")
            fb     = src.get("fallback")
            sent   = 0
            err    = 0

            # ۱. پردازش RSS
            items = await parse_rss_async(rss)
            total = len(items)
            print(f"📥 دریافت {total} آیتم از {name}")

            for item in items[:3]:
                link = item.get("link") or ""
                u = normalize_url(link)

                if not u or u in sent_urls or u in sent_now or u in bad_links:
                    log_skipped(name, u, "URL تکراری", item.get("title"))
                    continue

                try:
                    html = await fetch_html(session, link)
                    full = extract_full_content(html)
                    summ = summarize_text(full)

                    if is_garbage(full) or is_garbage(summ):
                        log_skipped(name, u, "محتوای بی‌کیفیت", item.get("title"))
                        log_garbage(name, link, item.get("title", ""), full)
                        bad_links.add(u)
                        err += 1
                        continue

                    cap = format_news(name, item.get("title", ""), summ, link)
                    h   = hashlib.md5(cap.encode("utf-8")).hexdigest()

                    if h in sent_hashes or h in hashes_now:
                        log_skipped(name, u, "خروجی تکراری", item.get("title"))
                        continue

                    await safe_send(bot, chat_id, cap, parse_mode="HTML")
                    sent_now.add(u)
                    hashes_now.add(h)
                    sent += 1

                except Exception as e:
                    log_skipped(name, u, f"خطا: {e}", item.get("title"))
                    print("⚠️ خطا در پردازش", link, "→", e)
                    bad_links.add(u)
                    err += 1

            # ۲. مدیریت fallback اگر RSS خالی بود
            if total == 0 and fb:
                try:
                    html_index = await fetch_html(session, fb)
                    soup = BeautifulSoup(html_index, "html.parser")
                    base = urlparse(fb)
                    links = []

                    # جمع‌آوری تا ۳ لینک یکتا از آرشیو
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("/"):
                            href = urlunparse(
                                (base.scheme, base.netloc, href, "", "", "")
                            )
                        if urlparse(href).netloc == base.netloc and href not in links:
                            links.append(href)
                        if len(links) >= 3:
                            break

                    for link in links:
                        u = normalize_url(link)
                        if not u or u in sent_urls or u in sent_now or u in bad_links:
                            log_skipped(name, u, "fallback تکراری", "fallback")
                            continue

                        try:
                            html = await fetch_html(session, link)
                            full = extract_full_content(html)
                            summ = summarize_text(full)

                            if is_garbage(full) or is_garbage(summ):
                                log_skipped(name, u, "fallback بی‌کیفیت", "fallback")
                                log_garbage(name, link, "fallback", full)
                                bad_links.add(u)
                                err += 1
                                continue

                            cap = format_news(
                                f"{name} - fallback",
                                "fallback",
                                summ,
                                link
                            )
                            h = hashlib.md5(cap.encode("utf-8")).hexdigest()

                            if h in sent_hashes or h in hashes_now:
                                log_skipped(name, u, "fallback تکراری", "fallback")
                                continue

                            await safe_send(bot, chat_id, cap, parse_mode="HTML")
                            hashes_now.add(h)
                            sent += 1

                        except Exception as fe:
                            log_skipped(name, link, f"خطا در fallback: {fe}", "fallback")
                            print("❌ خطا در fallback", name, "→", fe)
                            bad_links.add(u)
                            err += 1

                except Exception as e:
                    log_skipped(name, fb, f"fallback index error: {e}")
                    print("⚠️ خطا در دریافت fallback index:", e)
                    bad_links.add(fb)
                    err += 1

            stats.append({
                "منبع": name,
                "دریافت": total,
                "ارسال": sent,
                "خطا": err
            })

        # ذخیرهٔ نهایی وضعیت
        sent_urls.update(sent_now)
        sent_hashes.update(hashes_now)
        save_set(sent_urls, SENT_URLS_FILE)
        save_set(sent_hashes, SENT_HASHES_FILE)
        save_set(bad_links, BAD_LINKS_FILE)

        # ساخت و ارسال گزارش نهایی
        headers = ["Source", "Fetched", "Sent", "Errors"]
        widths  = {h: len(h) for h in headers}
        max_src = max((len(r["منبع"]) for r in stats), default=0)
        widths["Source"] = max(widths["Source"], max_src)

        for r in stats:
            widths["Fetched"] = max(widths["Fetched"], len(str(r["دریافت"])))
            widths["Sent"]    = max(widths["Sent"],    len(str(r["ارسال"])))
            widths["Errors"]  = max(widths["Errors"],  len(str(r["خطا"])))

        lines = [
            "📊 News Aggregation Report:\n",
            "  ".join(f"{h:<{widths[h]}}" for h in headers),
            "  ".join("-" * widths[h] for h in headers)
        ]
        for r in stats:
            row = [
                f"{r['منبع']:<{widths['Source']}}",
                f"{r['دریافت']:>{widths['Fetched']}}",
                f"{r['ارسال']:>{widths['Sent']}}",
                f"{r['خطا']:>{widths['Errors']}}"
            ]
            lines.append("  ".join(row))

        report = "<pre>" + "\n".join(lines) + "</pre>"
        await safe_send(bot, chat_id, report, parse_mode="HTML")
