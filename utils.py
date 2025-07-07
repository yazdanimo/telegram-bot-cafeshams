import json, re, feedparser, requests
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

def shorten_url(long_url):
    try:
        res = requests.get(f"https://is.gd/create.php?format=simple&url={long_url}")
        return res.text if res.status_code == 200 else long_url
    except:
        return long_url

def summarize_text(text):
    sentences = re.split(r"[.؟!]", text)
    full_sentences = [s.strip() for s in sentences if len(s.strip()) > 40]
    return ". ".join(full_sentences[:3])  # فقط ۳ جملهٔ اول

def format_news(name, title, summary, link):
    short_link = shorten_url(link)
    return (
        f"📡 {name}\n"
        f"<b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"🔗 <a href='{short_link}'>مشاهده خبر</a>\n\n"
        f"🆔 @cafeshamss\nکافه شمس ☕️🍪"
    )

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
        cleaned = summarize_text(text)
        if not cleaned or len(cleaned.strip()) < 50:
            print("⚠️ متن برای ترجمه کافی نیست")
            return text[:400]
        if not is_text_english(cleaned):
            print("⛔️ متن انگلیسی نیست → ترجمه نمی‌شه")
            return cleaned[:400]
        translated = translator.translate(cleaned, "Persian").result
        return translated.strip()
    except Exception as e:
        print(f"❌ خطا در ترجمه: {e}")
        return text[:400]
