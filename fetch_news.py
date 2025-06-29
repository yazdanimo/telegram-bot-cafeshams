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

def load_sent_titles():
    if not os.path.exists(STATS_FILE):
        return set()
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return set(data.get("sent_titles", []))
        except:
            return set()

def save_sent_title(title_hash):
    titles = load_sent_titles()
    titles.add(title_hash)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"sent_titles": list(titles)}, f, ensure_ascii=False, indent=2)

def make_hash(title):
    return hashlib.md5(title.lower().strip().encode("utf-8")).hexdigest()

def is_duplicate(title):
    return make_hash(title) in load_sent_titles()

def summarize(text, sentences_count=2):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join([str(sentence) for sentence in summary])
    except:
        return text

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

def translate_if_needed(text):
    if text.strip() == "":
        return ""
    try:
        if any('\u0600' <= ch <= '\u06FF' for ch in text):
            return text
        return translate(text)
    except:
        return text

def extract_image(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img["content"]:
            return og_img["content"]
    except:
        return None

def is_unique_content(title, summary):
    keywords = ["رویترز", "آسوشیتدپرس", "نقل", "بازنشر", "به گزارش", "به نقل از"]
    return not any(k in title or k in summary for k in keywords)

def load_sources():
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_news():
    sent_titles = load_sent_titles()
    sources = load_sources()
    all_news = []

    for source in sources:
        feed = feedparser.parse(source["url"])
        source_name = source["name"]

        for entry in feed.entries:
            title = entry.title.strip()
            link = entry.link
            summary = entry.get("summary", "").strip()

            if not title or is_duplicate(title):
                continue

            if not is_unique_content(title, summary):
                continue

            if len(summary) > 300:
                summary = summarize(summary)

            title_translated = translate_if_needed(title)
            summary_translated = translate_if_needed(summary)
            image_url = extract_image(link)

            title_hash = make_hash(title)
            save_sent_title(title_hash)

            news_item = {
                "source": source_name,
                "title": title_translated,
                "summary": summary_translated,
                "link": link,
                "image": image_url
            }

            all_news.append(news_item)

    return all_news
