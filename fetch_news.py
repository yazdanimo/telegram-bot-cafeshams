import requests
from bs4 import BeautifulSoup
from langdetect import detect
from translatepy import Translator
from utils import extract_full_content, extract_image_from_html
import json
import asyncio

translator = Translator()

# منابع خبری
with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

def summarize_text(text, max_chars=400):
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 50]
    joined = "\n".join(paragraphs[:3])
    return joined[:max_chars]

async def fetch_and_send_news(bot, chat_id, sent_urls):
    headers = { "User-Agent": "Mozilla/5.0" }

    for source in sources:
        name = source.get("name")
        url = source.get("url")

        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP خطا از {name}: {http_err}")
            continue
        except Exception as e:
            print(f"⚠️ خطا در دریافت RSS از {name}: {e}")
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

            ignore_keywords = ["فارسی", "العربية", "English", "تماس با ما", "تبلیغات", "آرشیو", "404", "Privacy", "فید خبر"]
            if any(word in full_text for word in ignore_keywords):
                print(f"⚠️ رد شد: محتوای قالب یا منو از {name}")
                continue

            try:
                lang = detect(title + full_text)
                if lang == "en":
                    title = translator.translate(title, "Persian").result
                    full_text = translator.translate(full_text, "Persian").result
            except Exception as e:
                print(f"⚠️ ترجمه انجام نشد از {name}: {e}")
                continue

            summary = summarize_text(full_text)

            caption = (
                f"📡 خبرگزاری {name}\n"
                f"{title}\n\n"
                f"{summary}\n\n"
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
                print(f"❗️ خطا در ارسال از {name}: {e}")

    return sent_urls
