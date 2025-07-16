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

SEND_INTERVAL      = 3
LAST_SEND          = 0
SENT_URLS_FILE     = "sent_urls.json"
SENT_HASHES_FILE   = "sent_hashes.json"
BAD_LINKS_FILE     = "bad_links.json"
SKIPPED_LOG_FILE   = "skipped_items.json"
GARBAGE_NEWS_FILE  = "garbage_news.json"
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
            items
            async def parse_rss_async(url):
    try:
        dp = await asyncio.wait_for(asyncio.to_thread(feedparser.parse, url), timeout=10)
        return dp.entries or []
    except Exception as e:
        print(f"⚠️ خطا در خواندن RSS {url}:", e)
        return []

async def fetch_html(session, url):
    async with session.get(url) as res:
        if res.status != 200:
            raise Exception(f"HTTP {res.status}")
        return await res.text()

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad_links  = load_set(BAD_LINKS_FILE)
    stats      = []
    sent_now   = set()
    hashes_now = set()

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        for src in load_sources():
            name, rss, fb = src.get("name"), src.get("rss"), src.get("fallback")
            sent = err = 0

            items = await parse_rss_async(rss)
            total = len(items)
            print(f"📥 دریافت {total} آیتم از {name}")

            for item in items[:3]:
                raw = item.get("link", "")
                u = normalize_url(raw)
                if not u or u in sent_urls or u in sent_now or u in bad_links:
                    log_skipped(name, u, "تکراری", item.get("title"))
                    continue

                try:
                    html = await fetch_html(session, raw)
                    full = extract_full_content(html)
                    summ = summarize_text(full)
                    if is_garbage(full) or is_garbage(summ):
                        log_skipped(name, u, "بی‌کیفیت", item.get("title"))
                        log_garbage(name, raw, item.get("title", ""), full)
                        bad_links.add(u)
                        err += 1
                        continue

                    cap = format_news(name, item.get("title", ""), summ, raw)
                    h = hashlib.md5(cap.encode("utf-8")).hexdigest()
                    if h in sent_hashes or h in hashes_now:
                        log_skipped(name, u, "تکراری", item.get("title"))
                        continue

                    await safe_send
                    
