import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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

    # حذف بخش‌های غیرمفید
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

    lines = [line.strip() for line in content.splitlines() if len(line.strip()) > 40]
    return "\n".join(lines[:15]) or "متن کامل قابل استخراج نبود."

def summarize_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:3]) or "خلاصه‌ای در دسترس نیست."

def format_news(source, title, summary, link):
    return (
        f"<b>{source}</b>\n\n"
        f"📰 <b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"🔗 <a href='{link}'>{link}</a>"
    )

def translate_text(text):
    try:
        response = requests.post(
            "https://translate.argosopentech.com/translate",
            json={"q": text, "source": "en", "target": "fa"},
            timeout=7
        )
        if response.status_code == 200:
            return response.json().get("translatedText", text)
    except Exception as e:
        print(f"⚠️ ترجمه انجام نشد → {e}")
    return text  # بازگشت به متن اصلی در صورت خطا

def is_persian(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))
