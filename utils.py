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
        print(f"❗️ خطا در استخراج تصویر: {e}")
        return None

def extract_full_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        candidates = soup.find_all(["p", "div"])
        full_text = " ".join(p.text for p in candidates if len(p.text.strip()) > 50)
        if len(full_text.strip()) < 100:
            print(f"⚠️ محتوای ناکافی از {url}")
            return "", []
        return full_text.strip(), []
    except Exception as e:
        print(f"❗️ خطا در دریافت محتوای کامل از: {url} → {e}")
        return "", []
