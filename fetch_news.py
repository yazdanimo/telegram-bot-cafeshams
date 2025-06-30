import feedparser
import hashlib
import json
import os
import requests
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from translate import Translator

STATS_FILE = "stats.json"
SOURCES_FILE = "sources.json"

def load_sent_titles():
    if not os.path.exists(STATS_FILE):
        print("⚠️ stats.json یافت نشد، ایجاد مجموعه خالی.")
        return set()
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return set(data.get("sent_titles", []))
        except:
            print("⚠️ خطا در خواندن stats.json")
            return set()

def save_sent_title(title_hash):
    titles = load_sent_titles()
    titles.add(title_hash)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"sent_titles": list(titles)}, f, ensure_ascii=False, indent=2)

def make_hash(title):
    return hashlib.md5(title.lower().strip().encode("utf-8")).hexdigest()

def is_duplicate(title):
    duplicate = make_hash(title) in load_sent_titles()
    if duplicate:
        print(f"⏩ رد شد (تکراری): {title}")
    return duplicate

def summarize(text, sentences_count=2):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join([str(sentence) for sentence in summary])
    except:
        return text

def translate(text, target_lang="fa"):
    try:
        translator = Translator(to_lang=target_lang)
        return translator.translate(text)
    except:
        return text

def translate_if_needed(text):
    if text.strip() == "":
        return ""
    try:
        if any('\u0600' <= ch <= '\u06FF' for ch in text):
            return text  # already in Persian
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

def load_sources():
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_and_send_news(app, group_id):
    print("🚀 اجرای fetch_and_send_news...")
    sent_titles = load_sent_titles()
    sources = load_sources()

    for source in sources:
        print(f"📡 بررسی منبع: {source['name']} - {source['url']}")
        feed = feedparser.parse(source["url"])

        for entry in feed.entries:
            title = entry.title.strip()
            link = entry.link
            summary = entry.get("summary", "").strip()
            print(f"🔍 بررسی خبر: {title}")

            if not title or is_duplicate(title):
                continue

            if len(summary) > 300:
                summary = summarize(summary)

            title_translated = translate_if_needed(title)
            summary_translated = translate_if_needed(summary)
            image_url = extract_image(link)

            title_hash = make_hash(title)
            save_sent_title(title_hash)

            text = f"\u2728 <b>{source['name']}</b>\n\uD83D\uDCC4 <b>{title_translated}</b>"
            if summary_translated:
                text += f"\n\n{summary_translated}"
            text += f"\n\n\uD83D\uDD17 <a href=\"{link}\">مشاهده خبر</a>"

            async def send():
                try:
                    await app.bot.send_message(chat_id=group_id, text=text, parse_mode="HTML", disable_web_page_preview=False)
                    print(f"✅ ارسال شد: {title_translated}")
                except Exception as e:
                    print(f"❌ خطا در ارسال: {e}")

            asyncio.create_task(send())

    print("✅ پایان fetch_and_send_news")
