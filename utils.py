# File: utils.py

import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# آدرس API ترجمه رایگان (LibreTranslate)
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

    content = ""
    for section in ["article", "main", "div", "section"]:
        el = soup.find(section)
        if el:
            content = el.get_text(separator=" ", strip=True)
            break

    if not content:
        content = soup.get_text(separator=" ", strip=True)

    lines = [ln.strip() for ln in content.splitlines() if len(ln.strip()) > 60]
    return "\n".join(lines[:10]) or "متن قابل استخراج نبود."

def summarize_text(text):
    paragraphs = text.split("\n\n")
    good = [p.strip() for p in paragraphs if len(p.strip()) > 80]
    return "\n\n".join(good[:2]) or "خلاصه‌ای در دسترس نیست."

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

def is_persian(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))

def format_news(source, title, summary, link):
    # همیشه عنوان و خلاصه را با ترجمه ارسال کن
    title_fa   = translate_text(title)
    summary_fa = translate_text(summary)

    return (
        f"📰 <b>{source}</b>\n\n"
        f"<b>{title_fa.strip()}</b>\n\n"
        f"{summary_fa.strip()}\n\n"
        f"🔗 <a href='{link}'>مشاهده کامل خبر</a>\n"
        f"🆔 @cafeshamss     \n"
        f"کافه شمس ☕️🍪"
    )
