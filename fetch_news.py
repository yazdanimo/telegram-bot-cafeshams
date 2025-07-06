import requests
from bs4 import BeautifulSoup
from langdetect import detect
from translatepy import Translator
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils import extract_full_content, extract_image_from_html
import json
import asyncio

translator = Translator()

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

def fix_named_entities(text):
    fixes = {
        "Boston Dynamics": "بوستون داینامیکس",
        "Santa Maria de Garoña": "سانتا ماریا دی گارونیا"
    }
    for en, fa in fixes.items():
        text = text.replace(en, fa)
    return text

def clean_messy_phrases(text):
    for phrase in ["در ۱۲ اوت در ۱۲ اوت", "با پرداخت هزینه ناعادلانه"]:
        text = text.replace(phrase, "")
    return text

def is_incomplete(text):
    bad_endings = ["...", "،", "برای گسترش", "در حالی که", "زیرا", "تا", "و", "که"]
    return any(text.strip().endswith(end) for end in bad_endings)

def clean_incomplete_sentences(text):
    lines = text.split("\n")
    return "\n".join([l.strip() for l in lines if len(l.strip()) > 30 and not is_incomplete(l)])

def fix_cutoff_translation(text):
    lines = text.split("\n")
    if lines and is_incomplete(lines[-1]):
        return "\n".join(lines[:-1])
    return text

def translate_text(text):
    try:
        raw = fix_named_entities(text)
        cleaned = clean_incomplete_sentences(clean_messy_phrases(raw))
        translated = translator.translate(cleaned, "Persian").result
        return fix_cutoff_translation(translated)
    except Exception as e:
        print(f"⚠️ خطا در ترجمه: {e}")
        return text[:400]

def assess_content_quality(text):
    paras = [p for p in text.split("\n") if len(p.strip()) > 40]
    return len(text) >= 300 and len(paras) >= 2

def extract_intro_paragraph(text):
    for para in text.split("\n"):
        if len(para.strip()) > 60 and not is_incomplete(para):
            return para.strip()
    return text.strip()[:300]

# 🔄 تابع اصلی دریافت و ارسال خبر
async def fetch_and_send_news(bot, chat_id, sent_urls, category_filter=None):
    headers = {"User-Agent": "Mozilla/5.0"}

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
            print(f"❌ خطا در RSS {name}: {e}")
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
                print(f"⚠️ رد شد: متن ضعیف از {name}")
                continue

            if any(word in full_text for word in ["تماس با ما", "Privacy", "404", "فید خبر"]):
                print(f"⚠️ رد شد: محتوای قالب یا تبلیغ از {name}")
                continue

            try:
                lang = detect(title + full_text)
                if lang == "en":
                    title = translate_text(title)
                    full_text = translate_text(full_text)
            except Exception as e:
                print(f"⚠️ ترجمه ناموفق از {name}: {e}")
                continue

            clean_text = clean_incomplete_sentences(full_text)
            intro = extract_intro_paragraph(clean_text)

            caption = (
                f"📡 خبرگزاری {name} ({category})\n"
                f"{title}\n\n"
                f"{intro}\n\n"
                f"🆔 @cafeshamss\nکافه شمس ☕️🍪"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 ادامه خبر", url=link)]
            ])

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024], reply_markup=keyboard)
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], reply_markup=keyboard)
                print(f"✅ ارسال موفق از {name}")
                sent_urls.add(link)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❗️ خطا در ارسال پیام از {name}: {e}")

    print(f"\n📊 مجموع خبرهای ارسال‌شده: {len(sent_urls)}")
    return sent_urls
