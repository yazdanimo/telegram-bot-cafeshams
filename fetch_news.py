import feedparser
from bs4 import BeautifulSoup

RSS_FEEDS = {
    "BBC": "https://feeds.bbci.co.uk/persian/rss.xml",
    "IRNA": "https://www.irna.ir/rss",
    "DW": "https://www.dw.com/fa-ir/rss",
    "Fars": "https://www.farsnews.ir/rss",
}

def extract_image(entry):
    # تلاش برای گرفتن تصویر از description
    soup = BeautifulSoup(entry.get("description", ""), "html.parser")
    img = soup.find("img")
    return img['src'] if img and img.has_attr("src") else None

def fetch_new_articles(seen_links):
    new_items = []

    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        if not feed.entries:
            continue

        for entry in feed.entries:
            title = entry.title.strip()
            link = entry.link.strip()
            summary = BeautifulSoup(entry.get("summary", ""), "html.parser").text.strip()
            image = extract_image(entry)

            if link in seen_links:
                continue

            new_items.append({
                "source": source,
                "title": title,
                "summary": summary,
                "link": link,
                "image": image
            })

    return new_items
