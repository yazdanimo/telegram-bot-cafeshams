
import aiohttp
from langdetect import detect
from deep_translator import GoogleTranslator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from bs4 import BeautifulSoup
import hashlib

sent_news_hashes = set()

def clean_text(text):
    return ' '.join(text.split())

async def fetch_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def async_translate(text, target="fa"):
    try:
        return GoogleTranslator(source="auto", target=target).translate(text)
    except:
        return text

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def summarize_text(text, sentence_count=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentence_count)
    return " ".join(str(sentence) for sentence in summary)

async def download_image(soup):
    img_tag = soup.find("img")
    if img_tag and img_tag.get("src", "").startswith("http"):
        return img_tag["src"]
    return None

def is_duplicate(unique_id):
    if unique_id in sent_news_hashes:
        return True
    sent_news_hashes.add(unique_id)
    return False
