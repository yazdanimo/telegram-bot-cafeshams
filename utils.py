from bs4 import BeautifulSoup

def extract_image_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # اولویت: تصویر از meta og:image یا twitter:image
    for prop in ["og:image", "twitter:image", "image"]:
        meta_tag = soup.find("meta", attrs={"property": prop}) \
                 or soup.find("meta", attrs={"name": prop}) \
                 or soup.find("meta", attrs={"itemprop": prop})
        if meta_tag and meta_tag.get("content"):
            return meta_tag["content"]

    # دومویت: تصویر از تگ <img> داخل محتوای خبری
    imgs = soup.find_all("img")
    for img in imgs:
        src = img.get("src")
        if src and src.startswith("http") and not any(x in src.lower() for x in ["logo", "icon", "banner", ".gif"]):
            return src

    # سومویت: تصویر داخل تگ <figure> یا <noscript>
    figure_img = soup.select_one("figure img")
    if figure_img and figure_img.get("src"):
        return figure_img["src"]

    noscript_img = soup.select_one("noscript img")
    if noscript_img and noscript_img.get("src"):
        return noscript_img["src"]

    return None
