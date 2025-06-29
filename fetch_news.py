import feedparser
import hashlib
import json
import os
import requests
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

STATS_FILE = "stats.json"
SOURCES_FILE = "sources.json"

# بارگذاری تیترهای قبلاً ارسال‌شده
def load_sent_titles():
    if not os.path.exists(STATS_FILE):
        return set()
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return set(data.get("sent_titles", []))
        except:
            return set()

# ذخیره هش تیتر
def save_sent_title(title_hash):
    titles = load_sent_titles()
    titles.add(title_hash)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"sent_titles": list(titles)}, f, ensure_ascii=False, indent=2)

def make_hash(title):
    return hashlib.md5(title.lower().strip().encode("utf-8")).hexdigest()

def is_duplicate(title):
    return make_hash(title) in load_sent_titles()

# خلاصه‌سازی متن خبر
def summarize(text, sentences_count=2):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join([str(sentence) for sentence in summary])
    except:
        return text

# ترجمه با LibreTranslate (رایگان و بدون کلید API)
def translate(text, source_lang="auto", target_lang="fa"):
    try:
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        return response.json()["translatedText"]
    except:
        return text

# اگر متن فارسی بود، ترجمه نمی‌کنه
def translate_if_needed(text):
    if text.strip() == "":
        return ""
    try:
        if any('\u0600' <= ch <= '\u06FF' for ch in text):
            return text
        return translate(text)
    except:
        retur
