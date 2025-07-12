# File: utils.py

import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

TRANSLATE_API_URL = "https://libretranslate.de/translate"

def load_sources(path="sources.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری {path} → {e}")
        return []

def parse_rss(url):
    feed = feedparser.parse(url)
    return feed.entries if feed and feed.entries else []

def extract_full_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()

    # پیدا کردن بخش‌های اصلی
    content = ""
    for section in ["article", "main", "div", "section"]:
        el = soup.find(section)
        if el:
            content = el.get_text(separator="\n", strip=True)
            break
    if not content:
        content = soup.get_text(separator="\n", strip=True)

    # فیلتر خطوط خیلی کوتاه، لینک یا تاریخ
    filtered = []
    for ln in content.splitlines():
        ln = ln.strip()
        if len(ln) < 60:
            continue
        if ln.startswith("http"):
            continue
        if re.match(r"^\d{1,2}\s+\w+\s+\d{4}", ln):
            continue
        filtered.append(ln)
    return " ".join(filtered)

def summarize_text(text):
    # دو جمله اول یا ۲۰۰ کاراکتر
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) >= 2:
        return " ".join(sentences[:2]).strip()
    return text.strip()[:200] + "..."

def is_persian(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))

def translate_text(text):
    try:
        resp = requests.post(
            TRANSLATE_API_URL,
            json={"q": text, "source": "en", "target": "fa", "format": "text"},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("translatedText", text)
    except Exception as e:
        print(f"⚠️ ترجمه انجام نشد → {e}")
    return text

def format_news(source, title, summary, link):
    # اگر عنوان یا خلاصه انگلیسی است، ترجمه کن
    if not is_persian(title):
        title = translate_text(title)
    if not is_persian(summary):
        summary = translate_text(summary)

    return (
        f"📰 <b>{source}</b>\n\n"
        f"<b>{title.strip()}</b>\n\n"
        f"{summary.strip()}\n\n"
        f"🔗 <a href='{link}'>مشاهده کامل خبر</a>\n"
        f"🆔 @cafeshamss     \n"
        f"کافه شمس ☕️🍪"
    )
