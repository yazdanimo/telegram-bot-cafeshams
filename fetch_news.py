import requests
from bs4 import BeautifulSoup
from langdetect import detect
from translatepy import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from utils import extract_full_content, extract_image_from_html
import json
import nltk
import asyncio

# 🧠 آماده‌سازی خلاصه‌سازی
nltk.download("punkt")

translator = Translator()

# 📚 بارگذاری منابع
with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

def summarize_text(text, sentence_count=4):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summary = LsaSummarizer()(parser.document, sentence_count)
        summarized = " ".join(str(sentence) for sentence in summary).strip()
        return summarized if len(summarized) > 100 else text[:400]
    except Exception as e:
        print(f"⚠️ خطا در خلاصه‌سازی: {e}")
        return text[:400]

async def fetch_and_send_news(bot, chat_id, sent_urls):
    headers = { "User-Agent": "Mozilla/5.0" }  # برای منابع محدود مثل Reuters

    for source in sources:
        name = source.get("name")
        url = source.get("url")

        try:
            rss = requests.get(url, timeout=10, headers=headers)
            rss.raise_for_status()
        except Exception as e:
            print(f"⚠️ خطا در دریافت RSS از {name}: {e}")
            continue

        soup = BeautifulSoup(rss.content, "xml")
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

            # رد محتوای ضعیف یا قالب سایت
            if not full_text or len(full_text.strip()) < 300:
                print(f"⚠️ رد شد: محتوای ناقص از {name}")
                continue
            garbage_keywords = ["فارسی", "العربية", "English", "تماس با ما", "تبلیغات", "آرشیو", "فید خبر", "کد استاتوس", "صفحه در دسترس نیست"]
            if any(word in full_text for word in garbage_keywords):
                print(f"⚠️ رد شد: محتوای قالب یا منوی سایت از {name}")
                continue

            try:
                lang = detect(title + full_text)
                if lang == "en":
                    title = translator.translate(title, "Persian").result
                    full_text = translator.translate(full_text, "Persian").result
            except Exception as e:
                print(f"⚠️ خطا در ترجمه یا زبان خبر از {name}: {e}")
                continue

            summary = summarize_text(full_text, 4)

            caption = (
                f"📡 خبرگزاری {name}\n"
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
                await asyncio.sleep(2)  # کنترل flood
            except Exception as e:
                print(f"❗️ خطا در ارسال از {name}: {e}")

    return sent_urls
