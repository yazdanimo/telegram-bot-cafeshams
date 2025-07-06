import requests
from bs4 import BeautifulSoup

# 📷 استخراج تصویر واقعی از HTML خبر
def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # 1️⃣ از metaها مثل og:image یا twitter:image
    for prop in ["og:image", "twitter:image", "image"]:
        meta_tag = (
            soup.find("meta", attrs={"property": prop}) or
            soup.find("meta", attrs={"name": prop}) or
            soup.find("meta", attrs={"itemprop": prop})
        )
        if meta_tag and meta_tag.get("content"):
            return meta_tag["content"]

    # 2️⃣ از تگ‌های <img> داخل محتوا
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith("http"):
            # رد تصاویر غیرخبر‌محور
            if not any(x in src.lower() for x in ["logo", "icon", "banner", ".gif"]):
                return src

    # 3️⃣ از <figure> یا <noscript>
    figure_img = soup.select_one("figure img")
    if figure_img and figure_img.get("src"):
        return figure_img["src"]

    noscript_img = soup.select_one("noscript img")
    if noscript_img and noscript_img.get("src"):
        return noscript_img["src"]

    return None

# 📄 استخراج متن کامل خبر از صفحه HTML
def extract_full_content(url):
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # کلاس‌هایی که معمولاً محتوای اصلی خبر رو دارن
        candidates = [
            "article-content", "news-body", "content", "item-text", "post-content",
            "entry-content", "story-body", "main-content", "body-text", "text"
        ]

        for cls in candidates:
            container = soup.find(class_=cls)
            if container:
                paragraphs = container.find_all("p")
                text = "\n".join(
                    p.get_text(strip=True)
                    for p in paragraphs
                    if len(p.get_text(strip=True)) > 30
                )
                return text, soup.title.string if soup.title else ""
        return "", ""
    except Exception as e:
        print(f"❌ خطا در دریافت متن کامل خبر: {e}")
        return "", ""
