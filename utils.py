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

        # تلاش برای یافتن بخش اصلی خبر (کلاس مقاله)
        article = soup.find(class_="news-body") or soup.find("article")
        if article:
            full_text = " ".join(p.text for p in article.find_all("p") if len(p.text.strip()) > 50)
        else:
            full_text = " ".join(p.text for p in soup.find_all("p") if len(p.text.strip()) > 50)

        full_text = full_text.strip()

        # محتوای غیرخبری یا ناقص
        garbage_keywords = [
            "فارسی", "العربية", "English",
            "تبلیغات", "آرشیو", "تماس با ما",
            "فید خبر", "صفحه در دسترس نیست",
            "Privacy Policy", "404", "کد استاتوس",
            "اینستاگرام", "توییتر", "آپارات", "روبیکا", "ایتا"
        ]

        if not full_text or len(full_text) < 300:
            print(f"⚠️ رد شد: متن ناکافی از {url}")
            return "", []

        if any(keyword in full_text for keyword in garbage_keywords):
            print(f"⚠️ رد شد: محتوای قالب یا منو از {url}")
            return "", []

        return full_text, []
    except Exception as e:
        print(f"❗️ خطا در دریافت یا پردازش صفحه: {url} → {e}")
        return "", []
