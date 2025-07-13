# File: fetch_news.py — نسخهٔ کامل نهایی با ثبت skipped items

import aiohttp
import asyncio
import json
import time
import hashlib
import feedparser
from urllib.parse import urlparse, urlunparse, parse_qsl
from utils import load_sources, extract_full_content, summarize_text, format_news

BAD_LINKS_FILE     = "bad_links.json"
SENT_URLS_FILE     = "sent_urls.json"
SENT_HASHES_FILE   = "sent_hashes.json"
GARBAGE_NEWS_FILE  = "garbage_news.json"
SKIPPED_LOG_FILE   = "skipped_items.json"
SEND_INTERVAL      = 3
LAST_SEND          = 0

def load_set(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_set(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

def normalize_url(url):
    p  = urlparse(url)
    qs = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith("utm_")]
    return urlunparse((p.scheme, p.netloc, p.path, "", "&".join(f"{k}={v}" for k, v in qs), ""))

def is_garbage(text):
    text = text.strip()
    return (
        len(text) < 60 or
        "ههههه" in text or
        "صف صف صف" in text or
        sum(text.count(ch) for ch in "؟%$#@!") > 5
    )

def log_garbage(source, link, title, content):
    try:
        with open(GARBAGE_NEWS_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except:
        existing = []
    existing.append({
        "source": source,
        "link": link,
        "title": title,
        "content": content[:300]
    })
    with open(GARBAGE_NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def log_skipped(source, url, reason, title=None):
    try:
        with open(SKIPPED_LOG_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    except:
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
    now = time.time()
    wait = SEND_INTERVAL - (now - LAST_SEND)
    if wait > 0:
        await asyncio.sleep(wait)
    try:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        print("⚠️ خطا در ارسال پیام →", e)
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
        print(f"⚠️ خطا در خواندن RSS → {url} →", e)
        return []

async def fetch_and_send_news(bot, chat_id, sent_urls, sent_hashes):
    bad_links  = load_set(BAD_LINKS_FILE)
    stats      = []
    sent_now   = set()
    hashes_now = set()

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        for src in load_sources():
            name, rss, fb = src.get("name"), src.get("rss"), src.get("fallback")
            sent, err, total = 0, 0, 0

            items = await parse_rss_async(rss)
            total = len(items)
            print(f"📥 دریافت {total} آیتم از {name}")

            if total == 0:
                err += 1
            else:
                for item in items[:3]:
                    raw = item.get("link") or ""
                    u   = normalize_url(raw)
                    if not u or u in sent_urls or u in sent_now or u in bad_links:
                        log_skipped(name, u, "URL already sent", item.get("title"))
                        continue

                    try:
                        async with session.get(raw) as res:
                            if res.status != 200:
                                raise Exception(f"HTTP {res.status}")
                            html = await res.text()

                        full = extract_full_content(html)
                        summ = summarize_text(full)
                        if is_garbage(full) or is_garbage(summ):
                            log_skipped(name, u, "Garbage content", item.get("title"))
                            log_garbage(name, raw, item.get("title", ""), full)
                            bad_links.add(u)
                            err += 1
                            continue

                        cap = format_news(name, item.get("title",""), summ, raw)
                        h   = hashlib.md5(cap.encode("utf-8")).hexdigest()
                        if h in sent_hashes or h in hashes_now:
                            log_skipped(name, u, "Duplicate hash", item.get("title"))
                            continue

                        await safe_send(bot, chat_id, cap, parse_mode="HTML")
                        sent_now.add(u)
                        hashes_now.add(h)
                        sent += 1

                    except Exception as e:
                        log_skipped(name, u, f"Exception: {str(e)}", item.get("title"))
                        print("⚠️ خطا در پردازش", raw, "→", e)
                        bad_links.add(u)
                        err += 1

            if total == 0 and fb:
                path = urlparse(fb).path
                if path in ["", "/", "/home", "/index", "/login", "/signup"]:
                    log_skipped(name, fb, "Bad fallback path")
                else:
                    try:
                        async with session.get(fb) as res:
                            if res.status != 200:
                                raise Exception(f"HTTP {res.status}")
                            html = await res.text()

                        full = extract_full_content(html)
                        summ = summarize_text(full)
                        if is_garbage(full) or is_garbage(summ):
                            log_skipped(name, fb, "Garbage fallback", "fallback")
                            log_garbage(name, fb, "fallback", full)
                            bad_links.add(fb)
                            err += 1
                        else:
                            cap = format_news(f"{name} - fallback", name, summ, fb)
                            h   = hashlib.md5(cap.encode("utf-8")).hexdigest()
                            if h in sent_hashes or h in hashes_now:
                                log_skipped(name, fb, "Duplicate fallback hash", "fallback")
                            else:
                                await safe_send(bot, chat_id, cap, parse_mode="HTML")
                                hashes_now.add(h)
                                sent += 1

                    except Exception as fe:
                        log_skipped(name, fb, f"Fallback exception: {str(fe)}", "fallback")
                        print("❌ خطا در fallback", name, "→", fe)
                        bad_links.add(fb)
                        err += 1

            stats.append({"منبع": name, "دریافت": total, "ارسال": sent, "خطا": err})

        sent_urls.update(sent_now)
        sent_hashes.update(hashes_now)
        save_set(sent_urls, SENT_URLS_FILE)
        save_set(sent_hashes, SENT_HASHES_FILE)
        save_set(bad_links, BAD_LINKS_FILE)

        # گزارش نهایی انگلیسی
        headers = ["Source", "Fetched", "Sent", "Errors"]
        widths  = {h: len(h) for h in headers}
        max_source_len = max(len(r["منبع"]) for r in stats)
        widths["Source"] = max(widths["Source"], max_source_len)
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
