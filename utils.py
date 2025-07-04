from bs4 import BeautifulSoup
import requests
import re

def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img")
    if img and img.get("src"):
        return img["src"]
    return None

def extract_full_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all(["p", "div"], recursive=True)
        full_text = " ".join(p.text for p in paragraphs if len(p.text.strip()) > 50)
        media_tags = soup.find_all(["video", "iframe", "img"])
        media_links = [tag.get("src") for tag in media_tags if tag.get("src")]
        return full_text.strip(), media_links
    except Exception as e:
        print(f"❗️ خطا در استخراج صفحه خبر: {url} → {e}")
        return "", []
