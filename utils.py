import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse

async def fetch_url(session, url):
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with session.get(url, timeout=timeout) as response:
            return await response.text()
    except Exception as e:
        print(f"⛔️ خطا در دریافت URL: {url} → {e}")
        return None

async def extract_news_title_and_image(html, source):
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # تلاش برای یافتن عنوان عمومی
        title = None
        for tag in [
            soup.find("meta", property="og:title"),
            soup.find("meta", attrs={"name": "title"}),
            soup.title
        ]:
            if tag:
                title = tag.get("content") or tag.string
                if title:
                    title = title.strip()
                    break

        # اگر هنوز title پیدا نشده
        if not title:
            # بررسی دامنه منبع خبر
            parsed = soup.find("meta", property="og:url")
            url = parsed["content"] if parsed else ""

            # استثنا برای IRNA
            if "irna.ir" in url:
                h1 = soup.find("h1", class_="title title-news")
                if h1 and h1.text:
                    title = h1.text.strip()

            # استثنا برای فارس و تسنیم
            if not title:
                h1_alt = soup.find("h1", class_=lambda x: x and "title" in x.lower())
                if h1_alt and h1_alt.text:
                    title = h1_alt.text.strip()

        if not title:
            title = "❗️ تیتر یافت نشد"

        full_title = f"{source} | {title}"

        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag else None

        return full_title, image_url

    except Exception as e:
        print(f"⛔️ خطا در پردازش HTML: {e}")
        return f"{source} | ❗️ خطا در دریافت تیتر", None
