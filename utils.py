import os
import sys
import json
import re
import logging
from bs4 import BeautifulSoup

BASE_DIR     = os.path.dirname(__file__)
SOURCES_PATH = os.path.join(BASE_DIR, "sources.json")

# 📥 بارگذاری منابع
def load_sources():
    if not os.path.exists(SOURCES_PATH):
        sys.exit(f"ERROR: sources.json not found at {SOURCES_PATH}")
    try:
        with open(SOURCES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: Invalid JSON in sources.json:\n  {e}")

# 📥 خواندن مجموعه‌های قبلی
def load_set(path: str) -> set:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

# 💾 ذخیره‌سازی مجموعه‌ها
def save_set(data: set, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)

# 📄 استخراج محتوای اصلی خبر
def extract_full_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")
    if article:
        return article.get_text("\n").strip()
    return "\n".join(p.get_text() for p in soup.find_all("p")).strip()

# 🧠 خلاصه‌سازی فارسی
def summarize_fa(text: str, max_s: int = 6) -> str:
    parts = re.split(r"[.؟!]\s*", text)
    summary = [p.strip() for p in parts if p.strip()]
    return " ".join(summary[:max_s])

# 🧠 خلاصه‌سازی انگلیسی
def summarize_en(text: str, max_s: int = 5) -> str:
    parts = re.split(r"[.?!]\s*", text)
    summary = [p.strip() for p in parts if p.strip()]
    return ". ".join(summary[:max_s])

# ✏️ قالب نهایی خبر برای تلگرام
def format_news(source: str, title: str, summary: str, link: str) -> str:
    clean_summary = summary.replace("\n", " ").strip()
    return (
        f"📰 {source}\n\n"
        f"**{title.strip()}**\n\n"
        f"{clean_summary}\n\n"
        f"🔗 [مشاهده کامل خبر]({link})\n"
        f"🆔 @cafeshamss — کافه شمس ☕️🍪"
    )

# 🧹 فیلتر صفحات بی‌ارزش
def is_garbage(text: str) -> bool:
    t = text.strip()
    if len(t) < 40:
        return True
    lower = t.lower()
    for kw in ["ثبت نام", "ورود", "login", "register", "signup", "رمز عبور"]:
        if kw in lower:
            return True
    return False

# ✅ ارسال ایمن پیام
async def safe_send(bot, chat_id, text, **kwargs):
    try:
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        logging.warning(f"❗️ Failed to send message: {e}")
