import requests
from bs4 import BeautifulSoup
from langdetect import detect
from translatepy import Translator
from utils import extract_full_content, extract_image_from_html
import json
import asyncio

translator = Translator()

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

# اصلاح اسامی خاص و عباراتی که ترجمه‌شون غلط می‌شه
def fix_named_entities(text):
    corrections = {
        "Araqchi": "عراقچی",
        "KSA": "عربستان سعودی",
        "Boston Dynamics": "بوستون داینامیکس",
        "Santa Maria de Garoña": "سانتا ماریا دی گارونیا"
    }
    for eng, fa in corrections.items():
        text = text.replace(eng, fa)
    return text

# حذف عباراتی که معنی ندارن یا تکراری هستن
def clean_messy_phrases(text):
    replacements = [
        "در ۱۲ اوت در ۱۲ اوت",
        "در تاریخ 12 اوت در 12 اوت",
        "با پرداخت هزینه ناعادلانه"
    ]
    for phrase in replacements:
        text = text.replace(phrase, "")
    return text

# تشخیص جمله‌های ناقص
def is_incomplete(text):
    bad_endings = ["...", "،", "بین دو", "برای گسترش", "در حالی که", "زیرا", "تا", "و", "که"]
    return any(text.strip().endswith(ending) for ending in bad_endings)

# حذف جمله‌های ناقص از متن
def clean_incomplete_sentences(text):
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if len(line.strip()) < 30 or is_incomplete(line):
            continue
        cleaned.append(line.strip())
    return "\n".join(cleaned)

# حذف جملهٔ آخر اگر ناقص بود
def fix_cutoff_translation(text):
    lines = text.split("\n")
    if lines and is_incomplete(lines[-1]):
        return "\n".join(lines[:-1])
    return text

# استخراج پاراگراف اول کامل، و ترجمه دقیق
def extract_intro_paragraph(text):
    for para in text.split("\n"):
        if len(para.strip()) > 60 and not is_incomplete(para):
            return para.strip()
    return text.strip()[:300]

# ترجمه با اصلاحات و حذف جمله‌های خراب
def translate_text(text):
    try:
        raw = fix_named_entities(text)
        messy = clean_messy_phrases(raw)
        cleaned = clean_incomplete_sentences(messy)
        translated = translator.translate(cleaned, "Persian").result
        return fix_cutoff_translation(translated)
    except Exception as e:
        print(f"⚠️ خطا در ترجمه: {e}")
        return text[:400]

# بررسی کیفیت کلی متن
def assess_content_quality(text):
    paragraph_count = len([p for p in text.split("\n") if len(p.strip()) > 40])
    character_count = len(text)
    return character_count >= 300 and paragraph_count >= 2

# تابع اصلی دریافت و ارسال خبر
async def fetch_and_send_news(bot, chat_id, sent_urls, category_filter=None):
    headers = {"User-Agent": "Mozilla/5.0"}

    for source in sources:
        name = source.get("name")
        url = source.get("url")
        category = source.get("category", "news")
        content_type = source.get("content_type", "text")

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

        for item in items[:5]:
            link = item.link.text.strip() if item.link else ""
            if not link or link in sent_urls:
                continue

            title = item.title.text.strip() if item.title else "بدون عنوان"
            raw_html = item.description.text.strip() if item.description else ""
            image_url = extract_image_from_html(raw_html)
            full_text, _ = extract_full_content(link)

            if not assess_content_quality(full_text):
                print(f"⚠️ رد شد: کیفیت متن پایین از {name}")
                continue

            garbage_keywords = ["تماس با ما", "فید خبر", "Privacy", "آرشیو", "404", "العربية"]
            if any(word in full_text for word in garbage_keywords):
                print(f"⚠️ رد شد: محتوای قالب یا تبلیغ از {name}")
                continue

            try:
                lang = detect(title + full_text)
                if lang == "en":
                    title = translate_text(title)
                    full_text = translate_text(full_text)
            except Exception as e:
                print(f"⚠️ خطا در تشخیص زبان یا ترجمه از {name}: {e}")
                continue

            clean_text = clean_incomplete_sentences(full_text)
            intro = extract_intro_paragraph(clean_text)

            caption = (
                f"📡 خبرگزاری {name} ({category})\n"
                f"{title}\n\n"
                f"{intro}\n\n"
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

    print(f"\n📊 مجموع ارسال‌شده‌ها: {len(sent_urls)}")
    return sent_urls
