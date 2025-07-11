import aiohttp
import asyncio
import json
import os
from utils import (
    load_sources,
    extract_full_content,
    summarize_text,
    format_news,
    translate_text,
    is_persian,
    parse_rss
)

BAD_LINKS_FILE = "bad_links.json"

def load_bad_links():
    if os.path.exists(BAD_LINKS_FILE):
        try:
            with open(BAD_LINKS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_bad_links(bad_links):
    with open(BAD_LINKS_FILE, "w") as f:
        json.dump(list(bad_links), f)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    sources = load_sources()
    bad_links = load_bad_links()
    report = []

    print("🚀 دیباگ آغاز شد: بررسی منابع خبری")

    for src in sources:
        name = src.get("name", "بدون‌نام")
        rss_url = src.get("rss")
        fallback = src.get("fallback")

        print(f"⏳ شروع بررسی {name}")

        try:
            items = parse_rss(rss_url)
            print(f"📥 دریافت {len(items)} آی
