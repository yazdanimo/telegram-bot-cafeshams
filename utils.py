import aiohttp
from bs4 import BeautifulSoup

async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            return await response.text()
    except:
        return None

async def extract_news_title_and_image(html, source):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title else "خبر جدید"
        img = soup.find("meta", property="og:image")
        image_url = img["content"] if img else None
        return f"{source} | {title}", image_url
    except:
        return f"{source} | خبر جدید", None
