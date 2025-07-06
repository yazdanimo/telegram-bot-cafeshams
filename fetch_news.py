import requests
from bs4 import BeautifulSoup

# 📷 استخراج تصویر از HTML یا متا
def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # تلاش اول: تصویر داخل HTML
    img = soup.find("img")
    if img and img.has_attr("src"):
        return img["src"]

    # تلاش دوم: متا OG تصویر
    meta_img = soup.find("meta", attrs={"property": "og:image"})
    if meta_img and meta_img.has_attr("content"):
        return meta_img["content"]

    # تلاش سوم: توییتر یا گوگل
    meta_img2 = soup.find("meta", attrs={"name": "twitter:image"})
    if meta_img2 and meta_img2.has_attr("content"):
        return meta_img2["content"]

    meta_img3 = soup.find("meta", attrs={"itemprop": "image"})
    if meta_img3 and meta_img3.has_attr("content"):
        return meta_img3["content"]

    return None

# 📄 استخراج متن کامل از صفحه خبر
def extract_full_content(url):
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        candidate_classes = [
            "article-content", "news-body", "content", "item-text", "post-content",
            "entry-content", "story-body", "article-body", "main-content", "body-text"
        ]

        for class_name in candidate_classes:
            content_div = soup.find(class_=class_name)
            if content_div:
                paragraphs = content_div.find_all("p")
                text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
                return text, soup.title.string if soup.title else ""
        return "", ""
    except Exception as e:
        print(f"❌ خطا در گرفتن محتوای کامل خبر از {url}: {e}")
        return "", ""
