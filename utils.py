from bs4 import BeautifulSoup
import requests

def extract_image_from_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
        return None
    except Exception as e:
        print(f"❗️ خطا در استخراج تصویر از HTML: {e}")
        return None

def extract_full_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        candidates = soup.find_all(["p", "div"])
        full_text = " ".join(p.text for p in candidates if len(p.text.strip()) > 50)
        if len(full_text.strip()) < 100:
            print(f"⚠️ محتوای ناکافی برای {url}")
            return "", []

        media_tags = soup.find_all(["video", "iframe", "img"])
        media_links = [tag.get("src") for tag in media_tags if tag.get("src")]
        return full_text.strip(), media_links
    except Exception as e:
        print(f"❗️ خطا در دریافت محتوای کامل از: {url} → {e}")
        return "", []
