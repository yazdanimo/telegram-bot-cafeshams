from bs4 import BeautifulSoup
import requests

def extract_image_from_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img")
        return img["src"] if img and img.get("src") else None
    except:
        return None

def extract_video_link(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        video = soup.find("iframe") or soup.find("video")
        return video["src"] if video and video.get("src") else None
    except:
        return None

def extract_full_content(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "html.parser")
        article = soup.find("article")
        paragraphs = []
        if article:
            for p in article.find_all("p"):
                text = p.get_text().strip()
                if len(text) > 40:
                    paragraphs.append(text)
        else:
            for p in soup.find_all("p"):
                text = p.get_text().strip()
                if len(text) > 40:
                    paragraphs.append(text)

        content = "\n".join(paragraphs)
        return content.strip(), res.url
    except:
        return "", url
