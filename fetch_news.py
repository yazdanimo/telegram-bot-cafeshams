import json
import feedparser
import requests
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from googletrans import Translator
from telegram import InputMediaPhoto
from datetime import datetime

seen_links = set()

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text()

def summarize_text(text, sentences_count=2):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join(str(sentence) for sentence in summary)

def translate_if_needed(text):
    translator = Translator()
    detected = translator.detect(text)
    if detected.lang == 'fa':
        return text
    elif detected.lang != 'en':
        text = translator.translate(text, dest='en').text
    return translator.translate(text, dest='fa').text

async def fetch_and_send_news(app, group_id):
    try:
        with open("data/sources.json", "r") as f:
            sources = json.load(f)

        for source in sources:
            url = source.get("url")
            name = source.get("name")
            if not url or not name:
                continue

            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get("link")
                title = clean_html(entry.get("title", ""))
                summary = clean_html(entry.get("summary", ""))
                published = entry.get("published", "")

                if link in seen_links or not title:
                    continue

                seen_links.add(link)

                translated_title = translate_if_needed(title)
                translated_summary = translate_if_needed(summary)
                final_summary = summarize_text(translated_summary)

                message = f"📰 {name} | {translated_title}\n\n📝 {final_summary}\n\n🔗 {link}"
                await app.bot.send_message(chat_id=group_id, text=message)

    except Exception as e:
        print("❌ خطا در دریافت یا ارسال خبر:", e)
