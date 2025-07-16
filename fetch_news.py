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

from translatepy import Translator

from utils import (
    load_sources,
    extract_full_content,
    summarize_text,
    format_news
)

# ── تنظیمات ───────────────────────────────────────────────────────────────

SEND_INTERVAL      = 3
LAST_SEND          = 0

SENT_URLS_FILE     = "sent_urls.json"
SENT_HASHES_FILE   = "sent_hashes.json"
BAD_LINKS_FILE     = "bad_links.json"
SKIPPED_LOG_FILE   = "skipped_items.json"
GARBAGE_NEWS_FILE  = "garbage_news.json"

translator = Translator()


# ── توابع کمکی ────────────────────────────────────────────────────────────

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
        if keyword in text.lower():
            return True
    return False


def log_garbage(source, link, title, content):
    try:
        with open(GARBAGE_NEWS_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        items = []
    items.append({
        "source":  source,
        "link":    link,
        "title":   title,
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
        "url":    url,
        "title":  title,
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


async def process_content(full_text: str, lang: str) -> str:
    """
    اگر متن انگلیسی بود، اول به فارسی ترجمه
    سپس خلاصه‌سازی؛ در غیر این صورت فقط خلاصه‌سازی.
    """
    text_for_summary = full_text
    if lang.lower() == "en":
        try:
            translation = await asyncio.to_thread(translator.translate,
                                                 full_text, "fa")
            # translatepy برمی‌گرداند یک شیء با فیلد .result
            text_for_summary = getattr(translation, "result", str(translation))
        except Exception as e:
            print("⚠️ خطا در ترجمه:", e)

    # خلاصه‌سازی (سینک با توابعutils)
    return await asyncio.to_thread(summarize_text, text_for_summary)


# ── تابع اصلی گردآوری و ارسال اخبار ────────────────────────────────────────

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
            lang = src.get("lang", "fa")  # "fa" یا "en"

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

            # ── fallback handling (مثل گذشته) ───────────────────────────────
            if total == 0 and fb:
                try:
                    html_index = await fetch_html(session, fb)
                    soup       = BeautifulSoup(html_index, "html.parser")
                    base       = urlparse(fb)
                    links      = []

                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("/"):
                            href = urlunparse((
                                base.scheme,
                                base.netloc,
                                href,
                                "",
                                "",
                                ""
                            ))
                        if urlparse(href).netloc == base
