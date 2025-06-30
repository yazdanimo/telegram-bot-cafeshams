import re
import aiohttp
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from langdetect import detect
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

sent_news = set()

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def fetch_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"

async def async_translate(text, target="fa"):
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except:
        return text

def summarize_text(text, sentences_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join(str(sentence) for sentence in summary)
    except:
        return text

async def download_image(soup):
    try:
        img = soup.find("img")
        if img and img.get("src") and img["src"].startswith("http"):
            return img["src"]
    except:
        pass
    return None

def is_duplicate(unique_id):
    if unique_id in sent_news:
        return True
    sent_news.add(unique_id)
    return False
