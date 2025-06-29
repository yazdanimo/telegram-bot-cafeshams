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

        # تلاش برای یافتن عنوان
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

        # اگر باز هم عنوان نداشت
        if not title:
            title = "❗️ تیتر یافت نشد"

        # منبع را اول تیتر اضافه کن
        full_title = f"{source} | {title}"

        # تصویر خبر
        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag else None

        return full_title, image_url

    except Exception as e:
        print(f"⛔️ خطا در تجزیه HTML برای خبر: {e}")
        return f"{source} | ❗️خطا در دریافت تیتر", None
