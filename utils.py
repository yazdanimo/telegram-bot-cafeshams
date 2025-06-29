import aiohttp
from bs4 import BeautifulSoup

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

        # اگر عنوان پیدا نشد، استثنا برای IRNA و فارس و تسنیم
        if not title:
            # IRNA
            h1_irna = soup.find("h1")
            if h1_irna and h1_irna.text:
                title = h1_irna.text.strip()

        if not title:
            # فارس و تسنیم
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
