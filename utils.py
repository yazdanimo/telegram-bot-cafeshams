import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from urllib.parse import urlparse

translator = Translator()

def load_sources():
    try:
        with open("sources.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری sources.json → {e}")
        return []

def parse_rss(url):
    feed = feedparser.parse(url)
    return feed.entries if feed and feed.entries else []

def extract_full_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()

    content = ""
    for tag_name in ["article", "main", "div", "section"]:
        el = soup.find(tag_name)
        if el:
            content = el.get_text(separator=" ", strip=True)
            break

    if not content:
        content = soup.get_text(separator=" ", strip=True)

    lines = [line.strip() for line in content.splitlines() if len(line.strip()) > 60]
    return "\n".join(lines[:10]) or "متن قابل استخراج نبود."

def summarize_text(text):
    paragraphs = text.split("\n\n")
    good = [p.strip() for p in paragraphs if len(p.strip()) > 80]
    return "\n".join(good[:2]) or "خلاصه‌ای در دسترس نیست."

def translate_text(text):
    try:
        result = translator.translate(text, src='en', dest='fa')
        return result.text
    except Exception as e:
        print(f"⚠️ ترجمه انجام نشد → {e}")
        return text

def is_persian(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))

def format_news(source, title, summary, link):
    return (
        f"📰 <b>{source}</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{summary.strip()}\n\n"
        f"🔗 <a href='{link}'>مشاهده خبر کامل</a>\n"
        f"🆔 @CafeShams"
    )
