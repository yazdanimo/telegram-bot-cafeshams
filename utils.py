import requests
from bs4 import BeautifulSoup

def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for prop in ["og:image", "twitter:image", "image"]:
        meta = (
            soup.find("meta", attrs={"property": prop}) or
            soup.find("meta", attrs={"name": prop}) or
            soup.find("meta", attrs={"itemprop": prop})
        )
        if meta and meta.get("content"):
            return meta["content"]

    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith("http"):
            if not any(x in src.lower() for x in ["logo", "icon", "banner", ".gif"]):
                return src

    figure_img = soup.select_one("figure img")
    if figure_img and figure_img.get("src"):
        return figure_img["src"]

    noscript_img = soup.select_one("noscript img")
    if noscript_img and noscript_img.get("src"):
        return noscript_img["src"]

    return None

def extract_video_link(html):
    soup = BeautifulSoup(html, "html.parser")

    iframe = soup.find("iframe")
    if iframe and iframe.get("src") and iframe["src"].startswith("http"):
        return iframe["src"]

    video_tag = soup.find("video")
    if video_tag:
        source = video_tag.find("source")
        if source and source.get("src") and source["src"].startswith("http"):
            return source["src"]

    return None

def extract_full_content(url):
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        response = requests.get(url, timeout=10, headers=headers)

        if response.status_code == 404 or "404" in response.text or "صفحه مورد نظر یافت نشد" in response.text:
            print("❌ 404 واقعی یا صفحه نامعتبر:", url)
            return "", ""

        soup = BeautifulSoup(response.content, "html.parser")

        candidates = [
            "news-body", "item-text", "article", "body", "entry-content", "story-body",
            "content-main", "text", "main-content", "article-content", "story-text",
            "post-content", "lead", "news-text", "mainText", "articleBody", "report-content",
            "newsContent", "contentInner", "detail-body", "item-body", "content-box", "main", "container"
        ]

        for cls in candidates:
            container = soup.find(class_=cls)
            if container:
                paragraphs = container.find_all("p")
                text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
                return text, soup.title.string if soup.title else ""

        article_tag = soup.find("article")
        if article_tag:
            paragraphs = article_tag.find_all("p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
            return text, soup.title.string if soup.title else ""

        return "", ""
    except Exception as e:
        print(f"❌ خطا در دریافت متن کامل خبر: {e}")
        return "", ""
