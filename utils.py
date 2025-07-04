from bs4 import BeautifulSoup
import re

def extract_image_from_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

        style_img = soup.find(style=re.compile("background.*url"))
        if style_img:
            match = re.search(r'url\((.*?)\)', style_img["style"])
            if match:
                return match.group(1).strip('"').strip("'")

        return None
    except Exception as e:
        print(f"❗️ خطا در استخراج تصویر: {e}")
        return None
