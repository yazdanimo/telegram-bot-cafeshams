import requests
from bs4 import BeautifulSoup

# 📷 استخراج تصویر از HTML یا متا
def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    img = soup.find("img")
    if img and img.has_attr("src"):
        return img["src"]

    for prop in ["og:image", "twitter:image", "image"]:
        meta = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop}) or soup.find("meta", attrs={"itemprop": prop})
        if meta and meta.has_attr("content"):
            return meta["content"]

    return None

# 📄 استخراج متن کامل از صفحهٔ خبر
def extract_full_content(url):
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        candidates = [
            "article-content", "news-body", "content", "item-text", "post-content",
            "entry-content", "story-body", "main-content", "body-text", "text"
        ]

        for cls in candidates:
            container = soup.find(class_=cls)
            if container:
                paragraphs = container.find_all("p")
                text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
                return text, soup.title.string if soup.title else ""
        return "", ""
    except Exception as e:
        print(f"❌ خطا در دریافت متن کامل خبر: {e}")
        return "", ""
