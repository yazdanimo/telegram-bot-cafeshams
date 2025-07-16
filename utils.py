import os
import sys
import json
from bs4 import BeautifulSoup
import re

BASE_DIR = os.path.dirname(__file__)
SOURCES_PATH = os.path.join(BASE_DIR, "sources.json")

def load_sources():
    if not os.path.exists(SOURCES_PATH):
        sys.exit(f"ERROR: فایل sources.json یافت نشد در {SOURCES_PATH}")
    try:
        with open(SOURCES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: JSON نامعتبر در sources.json:\n  {e}")

def load_set(path: str) -> set:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_set(data: set, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

def extract_full_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # اولویت به تگ <article>
    article = soup.find("article")
    if article:
        return article.get_text("\n").strip()
    # fallback: تمام <p>
    return "\n".join(p.get_text() for p in soup.find_all("p")).strip()

def summarize_text_fa(text: str, max_sentences: int = 2) -> str:
    # جداکردن بر اساس نقطه و علامت پایان جمله‌ی فارسی
    parts = re.split(r"[.؟!]", text)
    summary = []
    for p in parts:
        p = p.strip()
        if p:
            summary.append(p)
            if len(summary) >= max_sentences:
                break
    return "؛ ".join(summary)

def summarize_text_en(text: str, max_sentences: int = 2) -> str:
    parts = re.split(r"[.?!]", text)
    summary = []
    for p in parts:
        p = p.strip()
        if p:
            summary.append(p)
            if len(summary) >= max_sentences:
                break
    return ". ".join(summary)

def format_news(source: str, title: str, summary: str, link: str) -> str:
    return (
        f"<b>{source}</b>\n"
        f"<u>{title}</u>\n\n"
        f"{summary}\n\n"
        f"<a href=\"{link}\">ادامه خبر...</a>"
    )

def is_garbage(text: str) -> bool:
    # فقط متنی کمتر از 30 کاراکتر یا containing ثبت‌نام و spam
    t = text.strip()
    if len(t) < 30:
        return True
    lower = t.lower()
    for kw in ["ثبت نام", "ورود", "login", "register", "signup", "رمز عبور"]:
        if kw in lower:
            return True
    return False
