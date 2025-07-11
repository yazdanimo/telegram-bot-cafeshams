import asyncio
import json
from datetime import datetime
from telegram import Bot

from fetch_news import fetch_and_send_news          # منابع عمومی
from fetch_tasnim import fetch_tasnim_news          # منبع مستقل تسنیم
from editorial import generate_editorial            # سرمقاله روزانه

TOKEN = "توکن ربات رو اینجا بذار"
CHAT_ID_NEWS = "-100xxxxxxxxxx"         # کانال یا گروه خبری اصلی
CHAT_ID_EDITORIAL = "-100xxxxxxxxxx"    # گروه سردبیری

SENT_URLS_FILE = "sent_urls.json"

def load_sent_urls():
    try:
        with open(SENT_URLS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_sent_urls(sent_urls):
    with open(SENT_URLS_FILE, "w") as f:
        json.dump(list(sent_urls), f)

async def main_loop():
    print("🚀 ربات همه‌چی راه‌اندازی شد")
    bot = Bot(token=TOKEN)
    sent_urls = load_sent_urls()

    while True:
        try:
            print("✅ مرحله 1: دریافت منابع عمومی آغاز شد")
            await fetch_and_send_news(bot, CHAT_ID_NEWS, sent_urls)
            print("✅ مرحله 2: دریافت منابع عمومی انجام شد")

            print("⏳ مرحله 3: بررسی منبع اختصاصی Tasnim News")
            await fetch_tasnim_news(bot, CHAT_ID_NEWS, sent_urls)
            print("✅ مرحله 4: بررسی Tasnim انجام شد")

        except Exception as e:
            print(f"❌ خطا در دریافت خبرها → {e}")
            await bot.send_message(chat_id=CHAT_ID_NEWS, text=f"❗️ خطای دریافت خبرها → {e}")

        save_sent_urls(sent_urls)

        # 🕗 تولید سرمقاله روزانه ساعت ۲۰
        now = datetime.now()
        if now.hour == 20 and now.minute == 0:
            try:
                print("📝 تولید سرمقاله آغاز شد")
                await generate_editorial(bot, CHAT_ID_EDITORIAL)
            except Exception as ed_err:
                print(f"❌ خطا در تولید سرمقاله → {ed_err}")
                await bot.send_message(chat_id=CHAT_ID_EDITORIAL, text=f"❗️ خطای تولید سرمقاله → {ed_err}")

        # 📤 پایان دور اجرا
        await bot.send_message(chat_id=CHAT_ID_NEWS, text="🕒 چرخه اجرا کامل شد، صبر برای دور بعدی...")
        print("🕒 چرخه کامل شد، انتظار برای ۲۰۰ ثانیه...\n")

        await asyncio.sleep(200)  # زمان انتظار بین اجراها

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"❌ خطای کلی ربات → {e}")
