import json
import re
import feedparser
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
from translatepy import Translator

translator = Translator()
DetectorFactory.seed = 0

def load_sources():
    try:
        with open("sources.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ خطا در بارگذاری sources.json: {e}")
        return []

def parse_rss(url):
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries:
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", "")
            })
        return items
    except Exception as e:
        print(f"❌ خطا در parse_rss → {e}")
        return []

def extract_full_content(html):
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    content = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)
    return content.strip()

def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img")
    return img["src"] if img and img.has_attr("src") else None

def extract_video_link(html):
    soup = BeautifulSoup(html, "html.parser")
    video = soup.find("video")
    if video and video.has_attr("src"):
        return video["src"]
    iframe = soup.find("iframe")
    if iframe and iframe.has_attr("src"):
        return iframe["src"]
    return None

def assess_content_quality(text):
    paragraphs = [p for p in text.split("\n") if len(p.strip()) > 40]
    return len(text) >= 300 and len(paragraphs) >= 2

def clean_incomplete_sentences(text):
    sentences = re.split(r"[.؟!]", text)
    full_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    return ". ".join(full_sentences)

def fix_cutoff_translation(text):
    if not text:
        return ""
    return re.sub(r"(؟|،|؛|\.|!)$", "", text.strip())

def is_text_english(text):
    try:
        lang = detect(text.strip())
        keywords = ["the", "and", "in", "of", "for", "with"]
        has_keywords = any(kw in text.lower() for kw in keywords)
        return lang == "en" or has_keywords
    except:
        return False

def translate_text(text):
    try:
        cleaned = clean_incomplete_sentences(text)
        if not cleaned or len(cleaned.strip()) < 50:
            print("⚠️ متن برای ترجمه کافی نیست")
            return text[:400]
        if not is_text_english(cleaned):
            print("⛔️ متن انگلیسی نیست → ترجمه نمی‌شه")
            return cleaned[:400]
        translated = translator.translate(cleaned, "Persian").result
        fixed = fix_cutoff_translation(translated)
        return fixed.strip() if fixed else translated.strip()
    except Exception as e:
        print(f"❌ خطا در ترجمه: {e}")
        return text[:400]
