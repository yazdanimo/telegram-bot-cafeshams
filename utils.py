import requests
from bs4 import BeautifulSoup

def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img")
    return img["src"] if img and img.has_attr("src") else None

def extract_full_content(url):
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # لیست کلاس‌های احتمالی متن اصلی خبر
        content_classes = [
            "article-content", "news-body", "content", "item-text", "post-content",
            "entry-content", "story-body", "article-body", "main-content", "body-text"
        ]

        for class_name in content_classes:
            content_div = soup.find(class_=class_name)
            if content_div:
                paragraphs = content_div.find_all("p")
                text = "\n".join(p.get_text(strip=True) for p in paragraphs)
                return text, soup.title.string if soup.title else ""
        return "", ""
    except Exception as e:
        print(f"❌ خطا در گرفتن محتوای کامل خبر از {url}: {e}")
        return "", ""
