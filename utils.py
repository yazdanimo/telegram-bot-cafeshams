import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from googletrans import Translator

# مترجم محلی با googletrans
translator = Translator()

def load_sources(path="sources.json"):
    """بارگذاری لیست منابع خبری از فایل JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری {path} → {e}")
        return []

def parse_rss(url):
    """خواندن RSS و برگرداندن لیست آیتم‌ها."""
    feed = feedparser.parse(url)
    return feed.entries if feed and feed.entries else []

def extract_full_content(html):
    """استخراج متن اصلی صفحه با BeautifulSoup."""
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

    # فیلتر خطوط کوتاه
    lines = [ln.strip() for ln in content.splitlines() if len(ln.strip()) > 60]
    return "\n".join(lines[:10]) or "متن قابل استخراج نبود."

def summarize_text(text):
    """خلاصه واقعی با برش دو پاراگراف اول."""
    paras = text.split("\n\n")
    good = [p.strip() for p in paras if len(p.strip()) > 80]
    return "\n\n".join(good[:2]) or "خلاصه‌ای در دسترس نیست."

def translate_text(text):
    """ترجمه متن انگلیسی به فارسی با googletrans."""
    try:
        result = translator.translate(text, src="en", dest="fa")
        return result.text
    except Exception as e:
        print(f"⚠️ ترجمه انجام نشد → {e}")
        return text

def format_news(source, title, summary, link):
    """قالب‌بندی نهایی خبر برای ارسال به تلگرام."""
    # حتما لینک را قابل کلیک نگه‌دارید
    return (
        f"📰 <b>{source}</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{summary.strip()}\n\n"
        f"🔗 <a href='{link}'>مشاهده کامل خبر</a>\n"
        f"🆔 @CafeShams"
    )
