async def extract_news_title_and_image(html, source):
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # گرفتن عنوان حرفه‌ای‌تر
        title_tag = (
            soup.find("meta", property="og:title") or
            soup.find("meta", attrs={"name": "title"}) or
            soup.title
        )

        if title_tag:
            title = title_tag.get("content") or title_tag.string
            title = title.strip() if title else "خبر جدید"
        else:
            title = "خبر جدید"

        # گرفتن تصویر
        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag else None

        return f"{source} | {title}", image_url
    except Exception as e:
        print(f"خطا در استخراج تیتر/عکس: {e}")
        return f"{source} | خبر جدید", None
