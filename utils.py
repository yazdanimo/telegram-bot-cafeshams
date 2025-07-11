import feedparser
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import requests

def load_sources():
    # لیست منابع خبری از فایل sources.json
    try:
        with open("sources.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        print("⚠️ sources.json پیدا نشد یا خراب است")
        return []

def parse_rss(url):
    feed = feedparser.parse(url)
    if not feed or not feed.entries:
        return []
    return feed.entries

def extract_full_content(html):
    soup = BeautifulSoup(html, "html.parser")

    # حذف اسکریپت و استایل
    for script in soup(["script", "style"]):
        script.decompose()

    # تلاش برای پیدا کردن بخش اصلی
    content = ""
    for tag
