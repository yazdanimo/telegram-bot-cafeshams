import json
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
from translatepy import Translator

DetectorFactory.seed = 0
translator = Translator()

def load_sources():
    try:
        with open("sources.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ خطا در بارگذاری sources.json: {e}")
        return []

def parse_rss(url):
    try:
        feed = feedparser.parse(url)
        return [
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")
            }
            for entry in feed.entries
        ]
    except Exception as e:
        print(f"❌ خطا در parse_rss → {e}")
        return []

def extract_full_content(html):
    soup = BeautifulSoup(html, "html.parser")
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
    return "\n".join(paras).strip()

def shorten_url(long_url):
    try:
        r = requests.get(f"https://is.gd/create.php?format=simple&url={long_url}")
        return r.text if r.status_code == 200 else long_url
    except:
        return long_url

def summarize_text(text):
    sentences = re.split(r"[.؟!]", text)
    full = [s.strip() for s in sentences if len(s.strip()) > 40]
    return ". ".join(full[:3])

def is_persian(text):
    try:
        return detect(text.strip()) == "fa"
    except:
        return False

def is_text_english(text):
    try:
        return detect(text.strip()) == "en"
    except:
        return False

def translate_text(text):
    try:
        cleaned = summarize_text(text)
        if not cleaned:
            return text[:400]
        result = translator.translate(cleaned, "Persian").result
        return result.strip()
    except Exception as e:
        print(f"❌ خطای واقعی در ترجمه: {e}")
        return text[:400]

def format_news(name, title, summary, link):
    short = shorten_url(link)
    return (
        f"📡 {name}\n"
        f"<b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"🔗 <a href='{short}'>مشاهده خبر</a>\n\n"
        f"🆔 @cafeshamss\n"
        f"کافه شمس ☕️🍪"
    )
