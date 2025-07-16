# fetch_news.py

import aiohttp
import asyncio
import json
import time
import hashlib
import feedparser
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qsl

# نصب: pip install googletrans==4.0.0-rc1
from googletrans import Translator

from utils import load_sources, extract_full_content, summarize_text, format_news

SEND_INTERVAL      = 3
LAST_SEND          = 0
SENT_URLS_FILE     = "sent_urls.json"
SENT_HASHES_FILE   = "sent_hashes.json"
BAD_LINKS_FILE     = "bad_links.json"
SKIPPED_LOG_FILE   = "skipped_items.json"
GARBAGE_NEWS_FILE  = "garbage_news.json"

translator = Translator()


def load_set(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_set(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)


def normalize_url(url):
    p = urlparse(url)
    qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    query = "&".join(f"{k}={v}" for k, v in qs)
    return urlunparse((p.scheme, p.netloc, p.path, "", query, ""))


def is_garbage(text):
    text = text.strip()
    if len(text) < 60:
        return True
    persian = re.findall(r'[\u0600-\u06FF]', text)
    if len(persian) / max(len(text), 1) < 0.4:
        return True
    if re.search(r'(.)\1{5,}', text):
        return True
    if re.search(r'(ha){3,}|ههه{3,}', text):
        return True
    symbols = re.findall(r'[!?.،؛…]{2,}', text)
    if len(symbols) > 5:
        return True
    latin_words = re.findall(r'[A-Za-z]{5,}', text)
    if len(latin_words) > 5 and len(persian) < 50:
        return True
    for keyword in ["ثبت نام", "login", "register", "ورود", "signup", "رمز عبور"]:
        if keyword.lower() in text.lower():
            return True
    return False


def log_garbage(source, link, title, content):
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
    try:
        async with session.get(url) as res:
            if res.status != 200:
                raise Exception(f"HTTP {res.status}")
            return await res.text()
    except Exception as e:
        print(f"❌ خطا در دریافت HTML از {url}:", e)
        return ""


async def translate_to_farsi(text: str) -> str:
    try:
        # اجرا در thread تا event loop مسدود نشود
        result = await asyncio.to_thread(translator.translate, text, dest="fa")
        return result.text
    except Exception as e:
        print("⚠️ خطا در ترجمه:", e)
        return text


async def process_content(full_text: str, lang: str) -> str:
    """
    برای متون انگلیسی: اول ترجمه به فارسی، سپس خلاصه‌سازی
    برای متون فارسی: فقط خلاصه‌سازی
    """
    if lang == "en":
        fa_full = await translate_to_farsi(full_text)
        return await asyncio.to_thread(summarize_text, fa_full)
    else:
        return await asyncio.to_thread(summarize_text, full_text)


async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad_links   = load_set(BAD_LINKS_FILE)
    stats       = []
    sent_now    = set()
    hashes_now  = set()

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=20)
    ) as session:

        for src in load_sources():
            name = src.get("name")
            rss  = src.get("rss")
            fb   = src.get("fallback")
            lang = src.get("lang", "fa")  # مطمئن شو در sources.json هر منبع "lang": "en" یا "fa" دارد

            sent = err = 0
            items = await parse_rss_async(rss)
            total = len(items)
            print(f"📥 دریافت {total} آیتم از {name}")

            for item in items[:3]:
                raw = item.get("link", "")
                u   = normalize_url(raw)
                if not u or u in sent_urls or u in sent_now or u in bad_links:
                    log_skipped(name, u, "تکراری", item.get("title"))
                    continue

                try:
                    html = await fetch_html(session, raw)
                    full = extract_full_content(html)
                    summ = await process_content(full, lang)

                    if is_garbage(full) or is_garbage(summ):
                        log_skipped(name, u, "بی‌کیفیت", item.get("title"))
                        log_garbage(name, raw, item.get("title", ""), full)
                        bad_links.add(u)
                        err += 1
                        continue

                    caption = format_news(name, item.get("title", ""), summ, raw)
                    h       = hashlib.md5(caption.encode("utf-8")).hexdigest()

                    if h in sent_hashes or h in hashes_now:
                        log_skipped(name, u, "تکراری", item.get("title"))
                        continue

                    await safe_send(bot, chat_id, caption, parse_mode="HTML")
                    sent_now.add(u)
                    hashes_now.add(h)
                    sent += 1

                except Exception as e:
                    log_skipped(name, u, f"خطا: {e}", item.get("title"))
                    print("⚠️ خطا در پردازش", raw, "→", e)
                    bad_links.add(u)
                    err += 1

            # fallback handling (مثل قبل) ...

            stats.append({"منبع": name, "دریافت": total, "ارسال": sent, "خطا": err})

        # ذخیره و ارسال گزارش نهایی (مثل قبل) ...

        sent_urls.update(sent_now)
        sent_hashes.update(hashes_now)
        save_set(sent_urls,   SENT_URLS_FILE)
        save_set(sent_hashes, SENT_HASHES_FILE)
        save_set(bad_links,   BAD_LINKS_FILE)

        # ساخت و ارسال جدول گزارش نهایی
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
