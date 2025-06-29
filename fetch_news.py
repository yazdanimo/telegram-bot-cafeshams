import feedparser
import hashlib
import json
import os
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

STATS_FILE = "stats.json"
SOURCES_FILE = "sources.json"
LANGUAGES = ['en', 'fa']

translator = Translator()

# بارگذاری فهرست تیترهای قبلاً ارسال شده
def load_sent_titles():
    if not os.path.exists(STATS_FILE):
        return set()
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return set(data.get("sent_titles", []))
        except:
            return set()

# ذخیره تیتر جدید
def save_sent_title(title_hash):
    titles = load_sent_titles()
    titles.add(title_hash)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"sent_titles": list(titles)}, f, ensure_ascii=False, indent=2)

# بررسی اینکه خبر تکراریه یا نه
def is_duplicate(title):
    title_hash = hashlib.md5(title.lower().strip().encode("utf-8")).hexdigest()
    return title_hash in load_sent_titles()

def make_hash(title):
    return hashlib.md5(title.lower().strip().encode("utf-8")).hexdigest()

# خلاصه کردن متن خبر
def summarize(text, sentences_count=2):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join([str(sentence) for sentence in summary])

# تشخیص زبان و ترجمه
def translate_if_needed(text):
    detected = translator.detect(text).lang
    if detected not in LANGUAGES:
        return translator.translate(text, dest="en").text
    elif detected == "en":
        return translator.translate(text, dest="fa").text
    return text

# استخراج عکس از لینک خبر
def extract_image(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img["content"]:
            return og_img["content"]
    except:
        return None

# فیلتر کردن خبرهای غیرتولیدی یا بازنشرشده
def is_unique_content(title, summary):
    keywords = ["رویترز", "آسوشیتدپرس", "نقل", "بازنشر", "به گزارش", "به نقل از"]
    return not any(k in title or k in summary for k in keywords)

# خواندن منابع از sources.json
def load_sources():
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# پردازش و جمع‌آوری خبرها
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

            # خلاصه‌سازی
            if len(summary) > 300:
                summary = summarize(summary)

            # فیلتر اخبار بازنشر شده
            if not is_unique_content(title, summary):
                continue

            # ترجمه در صورت نیاز
            title_translated = translate_if_needed(title)
            summary_translated = translate_if_needed(summary)

            image_url = extract_image(link)

            # ذخیره هش تیتر
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
