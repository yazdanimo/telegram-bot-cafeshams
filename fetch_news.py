import requests
from bs4 import BeautifulSoup
from translatepy import Translator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from langdetect import detect
from utils import extract_image_from_html

# منبع تستی فقط: Mehr News
sources = [
    { "name": "Mehr News", "url": "https://www.mehrnews.com/rss" }
]

translator = Translator()

def summarize_text(text, sentence_count=4):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        summarized = " ".join(str(sentence) for sentence in summary).strip()
        return summarized if len(summarized) > 100 else text[:400]
    except Exception:
        return text[:400]

async def fetch_and_send_news(bot, chat_id, sent_urls):
    total_items = 0
    total_sent = 0

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

            # فقط فیلتر تیتر عکس بدون تصویر
            if title.startswith("عکس/") and not image_url:
                print(f"⚠️ خبر تصویری بدون عکس از {name} → رد شد")
                continue

            combined_text = f"{title}. {description}"
            try:
                lang = detect(combined_text)
            except:
                lang = "unknown"

            if lang not in ["fa", "en"]:
                try:
                    combined_text = translator.translate(combined_text, "English").result
                except:
                    pass

            summary = summarize_text(combined_text, sentence_count=4)

            if lang == "en":
                try:
                    title = translator.translate(title, "Persian").result
                    summary = translator.translate(summary, "Persian").result
                except:
                    pass

            caption = (
                f"📰 {name}\n"
                f"🔸 {title}\n\n"
                f"📃 {summary.strip()}\n\n"
                f"🖊 گزارش از {name} | 🆔 @cafeshamss     کافه شمس ☕️🍪"
            )

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024])
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096])
                print(f"✅ خبر ارسال شد از {name}")
                total_sent += 1
            except Exception as e:
                print(f"❗️ خطا در ارسال پیام از {name}: {e}")

    print("\n📊 گزارش تست:")
    print(f"🔹 خبر بررسی‌شده: {total_items}")
    print(f"🔹 ارسال موفق: {total_sent}")
