import requests
from bs4 import BeautifulSoup
from translatepy import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from langdetect import detect
from utils import extract_image_from_html
import json

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

translator = Translator()

def summarize_text(text, sentence_count=2):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentence_count)
    return " ".join(str(sentence) for sentence in summary)

async def fetch_and_send_news(bot, chat_id, sent_urls):
    any_news_sent = False
    total_items = 0
    total_duplicates = 0
    total_sent = 0

    for source in sources:
        url = source.get("url")
        name = source.get("name")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"⚠️ خطا در دریافت {name}: {e}")
            continue

        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all("item")
        print(f"\n📡 بررسی منبع: {name} → {url}")
        print(f"🔸 مجموع خبرها: {len(items)}")

        for item in items[:5]:
            title = item.title.text.strip() if item.title else "❗️ تیتر یافت نشد"
            link = item.link.text.strip() if item.link else ""
            description = item.description.text.strip() if item.description else ""
            image_url = extract_image_from_html(description)

            if not link or link in sent_urls:
                total_duplicates += 1
                continue

            sent_urls.add(link)
            total_items += 1

            text_to_process = f"{title}. {description}"
            try:
                lang = detect(text_to_process)
            except:
                lang = "unknown"

            if lang not in ["en", "fa"]:
                try:
                    text_to_process = translator.translate(text_to_process, "English").result
                    print("🌐 ترجمه اولیه به انگلیسی انجام شد.")
                except Exception as e:
                    print(f"❗️ خطا در ترجمه به انگلیسی: {e}")
                    continue

            try:
                summary = summarize_text(text_to_process)
            except:
                summary = text_to_process[:400]

            if lang == "en":
                try:
                    summary = translator.translate(summary, "Persian").result
                except Exception as e:
                    print(f"❗️ خطا در ترجمه نهایی به فارسی: {e}")

            # ✂️ کوتاه‌سازی لینک در صورت طولانی بودن
            short_link = link[:50] + "..." if len(link) > 60 else link

            # 📝 کپشن نهایی با تگ برند
            caption = f"🗞 {name}\n\n🔹 {title}\n\n📌 {summary}\n\n🌐 {short_link}\n\n@cafeshamss"

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024])
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096])
                print(f"✅ خبر ارسال شد از {name}")
                any_news_sent = True
                total_sent += 1
            except Exception as e:
                print(f"❗️ خطا در ارسال خبر: {e}")

    print("\n📊 آمار اجرای فعلی:")
    print(f"🔹 تعداد کل منابع: {len(sources)}")
    print(f"🔹 خبرهای جدید ارسال‌شده: {total_sent}")
    print(f"🔹 خبرهای تکراری: {total_duplicates}")
    print(f"🔹 جمع خبرهای بررسی‌شده: {total_items + total_duplicates}")
    if not any_news_sent:
        print("⚠️ در این نوبت هیچ خبری ارسال نشد.")

    return sent_urls
