import feedparser
import hashlib
import json
import os

def fetch_new_articles():
    with open("sources.json", "r", encoding="utf-8") as f:
        sources = json.load(f)

    if not os.path.exists("data/stats.json"):
        stats = {"seen_hashes": []}
    else:
        with open("data/stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)

    new_articles = []

    for source in sources:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            lang = source.get("lang", "en")

            content_hash = hashlib.sha256(f"{title}{link}".encode()).hexdigest()

            if content_hash in stats["seen_hashes"]:
                continue

            stats["seen_hashes"].append(content_hash)

            new_articles.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": source["name"],
                "lang": lang
            })

    stats["seen_hashes"] = stats["seen_hashes"][-1000:]

    with open("data/stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return new_articles

