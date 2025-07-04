import requests
from bs4 import BeautifulSoup
from translatepy import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from langdetect import detect
from utils import extract_image_from_html
import json

# بارگذاری منابع
with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

translator = Translator()

def summarize_text(text, sentence_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        return " ".join(str(sentence) for sentence in summary)
    except Exception:
        return text[:400]

async def fetch_and_send_news(bot, chat_id, sent_urls):
    total_items = 0
    total_duplicates = 0
    total_sent = 0
    any_news_sent = False

    for source in sources:
        name = source.get("name")
        url = source.get("url")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"⚠️ خطا در دریافت {name}: {e}")
            continue

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")
        print(f"\n📡 بررسی منبع: {name} → {url}")
        print(f"🔸 مجموع خبرها: {len(items)}")

        for item in items[:5]:
            title = item.title.text.strip() if item.title else "بدون عنوان"
            link = item.link.text.strip() if item.link else ""
            description = item.description.text.strip() if item.description else ""
            image_url = extract_image_from_html(description)

            # فیلتر تیترهای تکراری یا بدون لینک
            if not link or link in sent_urls:
                total_duplicates += 1
                continue

            sent_urls.add(link)
            total_items += 1

            # فیلتر تیترهایی که با "عکس/" شروع می‌شن اما تصویر ندارن
            if title.startswith("عکس/") and not image_url:
                print(f"⚠️ خبر تصویری بدون عکس از {name} → رد شد")
                continue

            # پردازش متن خبر برای تشخیص زبان و خلاصه‌سازی
            combined_text = f"{title}. {description}"
            try:
                lang = detect(combined_text)
            except:
                lang = "unknown"

            if lang not in ["en", "fa"]:
                try:
                    combined_text = translator.translate(combined_text, "English").result
                except:
                    pass

            summary = summarize_text(combined_text, sentence_count=3)

            if lang == "en":
                try:
                    summary = translator.translate(summary, "Persian").result
                except:
                    pass

            # ساخت کپشن نهایی بدون لینک
            caption = (
                f"📰 {name}\n"
                f"🔸 {title.strip()}\n\n"
                f"📃 {summary.strip()}\n\n"
                f"🖊 گزارش از {name} | @cafeshamss"
            )

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024])
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096])
                print(f"✅ خبر ارسال شد از {name}")
                total_sent += 1
                any_news_sent = True
            except Exception as e:
                print(f"❗️ خطا در ارسال پیام از {name}: {e}")

    print("\n📊 آمار اجرای فعلی:")
    print(f"🔹 تعداد منابع بررسی‌شده: {len(sources)}")
    print(f"🔹 خبرهای ارسال‌شده: {total_sent}")
    print(f"🔹 خبرهای تکراری: {total_duplicates}")
    if not any_news_sent:
        print("⚠️ هیچ خبری ارسال نشد.")

    return sent_urls
