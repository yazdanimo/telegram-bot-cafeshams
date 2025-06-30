import requests

def download_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"❗️ خطا در دانلود تصویر: {e}")
    return None
import re

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)  # حذف فاصله‌های اضافه
    text = re.sub(r'\u200c', '', text)  # حذف نیم‌فاصله
    return text.strip()
from deep_translator import GoogleTranslator
from langdetect import detect

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

async def async_translate(text, target_lang="en"):
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as e:
        print(f"Translation failed: {e}")
        return text
        import aiohttp

async def fetch_url(session, url):
    async with session.get(url, timeout=10) as response:
        return await response.text()
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

def summarize_text(text, sentences_count=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join([str(sentence) for sentence in summary])
