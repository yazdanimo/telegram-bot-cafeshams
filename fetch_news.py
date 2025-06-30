import feedparser
import json
import requests
from bs4 import BeautifulSoup
from telegram import InputMediaPhoto
from googletrans import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import hashlib
import os
from datetime import datetime

translator = Translator()

SEEN_PATH = "data/seen.json"
SOURCE_PATH = "data/sources.json"

if not os.path.exists(SEEN_PATH):
    with open(SEEN_PATH, "w") as f:
        json.dump([], f)

def load_sources():
    with open(SOURCE_PATH, "r") as f:
        return json.load(f)

def load_seen():
    with open(SEEN_PATH, "r") as f:
        return json.load(f)

def save_seen(seen):
    with open(SEEN_PATH, "w") as f:
        json.dump(seen, f)

def get_article_image(link):
    try:
        response = requests.get(link, timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]
    except:
        return None

def translate_text(text, target_lang="fa"):
    try:
        result = translator.translate(text, dest=target_lang)
        return result.text
    except:
        return text

def summarize_text(text, sentences_count=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join([str(sentence) for sentence in summary])

def create_uid(title, link):
    return hashlib.md5((title + link).encode()).hexdigest()

def fetch_and_send_news(bot, chat_id):
    sources = load_sources()
    seen = load_seen()
    new_seen = seen.copy()
    count = 0

    for source in sources:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:3]:  # حداکثر ۳ خبر از هر منبع
                title = entry.title.strip()
                link = entry.link
                uid = create_uid(title, link)

                if uid in seen:
                    continue

                content = entry.get("summary", "") or entry.get("description", "")
                image_url = get_article_image(link)

                is_fa = False
                try:
                    is_fa = translator.detect(title).lang == "fa"
                except:
                    pass

                if not is_fa:
                    title = translate_text(title)
                    content = translate_text(content)

                summary = summarize_text(content) if not is_fa else content
                message = f"<b>{source['name']}</b> | <b>{title}</b>\n\n{summary}\n\n<a href='{link}'>لینک خبر</a>"

                try:
                    if image_url:
                        bot.send_photo(chat_id=chat_id, photo=image_url, caption=title, parse_mode="HTML")
                        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML", disable_web_page_preview=True)
                    else:
                        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML", disable_web_page_preview=True)
                    new_seen.append(uid)
                    count += 1
                except Exception as e:
                    print("❌ Error sending message:", e)
        except Exception as e:
            print(f"❌ Failed to process source {source['name']}:", e)

    save_seen(new_seen)
    print(f"✅ {count} خبر ارسال شد. [{datetime.now()}]")
