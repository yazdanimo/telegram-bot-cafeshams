from bs4 import BeautifulSoup
import re

def extract_image_from_html(html):
    """
    تلاش برای یافتن آدرس اولین تصویر از HTML توضیحات خبر.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        # اول از همه دنبال تگ img می‌گردیم
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

        # اگر تگ img نبود، شاید تصویر در background باشد
        style_img = soup.find(style=re.compile("background.*url"))
        if style_img:
            match = re.search(r'url\((.*?)\)', style_img["style"])
            if match:
                url = match.group(1).strip('"').strip("'")
                return url

        return None
    except Exception as e:
        print(f"❗️ خطا در استخراج تصویر: {e}")
        return None
