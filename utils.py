from bs4 import BeautifulSoup
import aiohttp

# گرفتن HTML صفحه
async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"⛔️ خطا در دریافت {url}: {response.status}")
                return ""
    except Exception as e:
        print(f"⛔️ خطای شبکه برای {url}: {e}")
        return ""

# گرفتن تیتر، تصویر، متن خبر
async def extract_news_title_image_text(html, source, url):
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # تیتر خبر
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

        # مخصوص ایرنا
        if not title and "irna.ir" in url:
            h1 = soup.find("h1", class_="title title-news")
            if h1 and h1.text:
                title = h1.text.strip()

        # حالت عمومی h1
        if not title:
            h1_alt = soup.find("h1", class_=lambda x: x and "title" in x.lower())
            if h1_alt and h1_alt.text:
                title = h1_alt.text.strip()

        if not title:
            title = "❗️ تیتر یافت نشد"

        full_title = f"{source} | {title}"

        # تصویر
        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag else None

        # متن خبر
        description = None
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            description = desc_tag["content"].strip()
        else:
            first_p = soup.find("p")
            if first_p and first_p.text:
                description = first_p.text.strip()

        return full_title, image_url, description or ""

    except Exception as e:
        print(f"⛔️ خطا در تحلیل HTML: {e}")
        return f"{source} | ❗️ خطا در دریافت تیتر", None, ""
