# utils.py

import json
from bs4 import BeautifulSoup


def load_sources():
    with open("sources.json", encoding="utf-8") as f:
        return json.load(f)


def load_set(path: str) -> set:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def save_set(data: set, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)


def extract_full_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")
    if article:
        return article.get_text("\n")
    ps = soup.find_all("p")
    return "\n".join(p.get_text() for p in ps)


def summarize_text(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return lines[0] if lines else text[:200]


def format_news(source: str, title: str, summary: str, link: str) -> str:
    return (
        f"<b>{source}</b>\n"
        f"<b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"<a href=\"{link}\">ادامه خبر...</a>"
    )
