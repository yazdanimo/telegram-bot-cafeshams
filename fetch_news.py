import requests
from bs4 import BeautifulSoup
from langdetect import detect
from translatepy import Translator
from utils import extract_full_content, extract_image_from_html
import json
import asyncio

translator = Translator()

# 👇 بارگذاری منابع خبری دسته‌بندی‌شده
with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

def summarize_text(text, max_chars=400):
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 50]
    return "\n".join(paragraphs[:3])[:max_chars]

def fix_named_entities(text):
    corrections = {
        "Araqchi": "عراقچی",
        "KSA": "عربستان سعودی",
        "Aliza Enati": "علیزا اناتی",
        "Faisal bin Farhan": "فیصل بن فرحان",
        "Walid bin Abdulkarim Al-Khulaifi": "ولید بن عبدالکریم الخلیفی"
    }
    for eng, fa in corrections.items():
        text = text.replace(eng, fa)
    return text

def clean_incomplete_sentences(text):
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if len(line.strip()) < 20 or line.strip().endswith(("...", "بین دو", "،")):
            continue
        cleaned.append(line.strip())
    return "\n".join(cleaned)

def translate_text(text):
    try:
        raw = fix_named_entities(text)
        cleaned = clean_incomplete_sentences(raw)
        translated = translator.translate(cleaned, "Persian").result
        return translated
    except Exception as e:
        print(f"⚠️ خطا در ترجمه: {e}")
        return text[:400]

async def fetch_and_send_news(bot, chat_id, sent_urls, category_filter=None):
    headers = { "User-Agent": "Mozilla/5.0" }

    for source in sources:
        name = source.get("name")
        url = source.get("url")
        category = source.get("category", "news")

        if category_filter and category != category_filter:
            continue

        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ خطا در دریافت RSS از {name}: {e}")
            continue

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")
        print(f"\n📡 دریافت RSS از {name} → مجموع: {len(items)}")

        for item in items[:3]:
            link = item.link.text.strip() if item.link else ""
            if not link or link in sent_urls:
                continue

            title = item.title.text.strip() if item.title else "بدون عنوان"
            raw_html = item.description.text.strip() if item.description else ""
            image_url = extract_image_from_html(raw_html)
            full_text, _ = extract_full_content(link)

            if not full_text or len(full_text) < 300:
                print(f"⚠️ رد شد: متن ناکافی یا ضعیف از {name}")
                continue

            garbage_keywords = ["تماس با ما", "فید خبر", "Privacy", "آرشیو", "404", "العربية"]
            if any(word in full_text for word in garbage_keywords):
                print(f"⚠️ رد شد: محتوای قالب یا منو از {name}")
                continue

            try:
                lang = detect(title + full_text)
                if lang == "en":
                    title = translate_text(title)
                    full_text = translate_text(full_text)
            except Exception as e:
                print(f"⚠️ خطا در تشخیص زبان یا ترجمه از {name}: {e}")
                continue

            summary = summarize_text(full_text)

            caption = (
                f"📡 خبرگزاری {name} ({category})\n"
                f"{title}\n\n"
                f"{summary.strip()}\n\n"
                f"🆔 @cafeshamss\nکافه شمس ☕️🍪"
            )

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024])
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096])
                print(f"✅ خبر ارسال شد از {name}")
                sent_urls.add(link)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❗️ خطا در ارسال خبر از {name}: {e}")

    return sent_urls
