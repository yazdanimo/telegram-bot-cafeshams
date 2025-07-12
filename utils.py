# File: utils.py

import feedparser
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

LIBRE_URL   = "https://libretranslate.de/translate"
GOOGLE_URL  = "https://translate.googleapis.com/translate_a/single"

def load_sources(path="sources.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def parse_rss(url):
    feed = feedparser.parse(url)
    return feed.entries or []

def extract_full_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","header","footer","nav"]):
        tag.decompose()
    content = ""
    for name in ("article","main","div","section"):
        el = soup.find(name)
        if el:
            content = el.get_text(separator="\n", strip=True)
            break
    if not content:
        content = soup.get_text(separator="\n", strip=True)
    lines = [
        ln.strip()
        for ln in content.splitlines()
        if len(ln.strip()) > 60
        and not ln.startswith("http")
        and not re.match(r"^\d{1,2}\s+\w+\s+\d{4}", ln.strip())
    ]
    return " ".join(lines)

def summarize_text(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) >= 2:
        return " ".join(sentences[:2]).strip()
    return text.strip()[:200] + "..."

def is_english(text):
    return bool(re.search(r"[A-Za-z]", text))

def translate_with_libre(text):
    try:
        r = requests.post(
            LIBRE_URL,
            json={"q": text, "source": "en", "target": "fa", "format": "text"},
            timeout=8
        )
        if r.status_code == 200:
            return r.json().get("translatedText", text)
    except:
        pass
    return text

def translate_with_google(text):
    try:
        params = {"client":"gtx","sl":"en","tl":"fa","dt":"t","q":text}
        r = requests.get(GOOGLE_URL, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        return "".join(seg[0] for seg in data[0])
    except:
        return text

def translate_text(text):
    if not is_english(text):
        return text
    t = translate_with_libre(text)
    if t and t != text:
        return t
    return translate_with_google(text)

def format_news(source, title, summary, link):
    title = translate_text(title)
    summary = translate_text(summary)
    return (
        f"📰 <b>{source}</b>\n\n"
        f"<b>{title.strip()}</b>\n\n"
        f"{summary.strip()}\n\n"
        f"🔗 <a href='{link}'>مشاهده کامل خبر</a>\n"
        f"🆔 @cafeshamss     \n"
        f"کافه شمس ☕️🍪"
    )
