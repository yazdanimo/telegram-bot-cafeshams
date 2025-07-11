from datetime import datetime
import json
import os
import random

SENT_URLS_FILE = "sent_urls.json"

def load_sent_urls():
    if os.path.exists(SENT_URLS_FILE):
        try:
            with open(SENT_URLS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def filter_today_links(urls):
    today = datetime.now().strftime("%Y/%m/%d")
    return [url for url in urls if today in url]

async def generate_editorial(bot, chat_id):
    all_urls = load_sent_urls()
    today_links = filter_today_links(all_urls)

    if not today_links:
        await bot.send_message(chat_id=chat_id, text="❗️امروز خبری دریافت نشده. سرمقاله تولید نشد.")
        return

    chosen_link = random.choice(today_links)

    today_str = datetime.now().strftime("%Y/%m/%d")
    title = f"📰 سرمقاله روز - {today_str}"
    body = (
        f"امروز یکی از خبرهای برجسته در فضای خبری ایران منتشر شد:\n\n"
        f"🔗 <a href='{chosen_link}'>{chosen_link}</a>\n\n"
        f"این خبر بازتاب قابل توجهی در رسانه‌ها داشت و نشان‌دهندهٔ حساسیت افکار عمومی نسبت به تحولات جاری است. "
        f"سرمقالهٔ امروز تأکیدی بر اهمیت این اتفاق و بازتاب آن در روندهای آینده دارد.\n\n"
        f"📝 تحلیل تخصصی در نسخه‌های بعدی ارائه خواهد شد.\n"
        f"🆔 @cafeshamss"
    )

    await bot.send_message(chat_id=chat_id, text=body, parse_mode="HTML")
