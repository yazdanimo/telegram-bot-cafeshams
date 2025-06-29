import os
import asyncio
from telegram import Bot, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from fetch_news import fetch_new_articles
from utils import load_stats, mark_as_sent, has_been_sent

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int("-1002514471809")
bot = Bot(token=BOT_TOKEN)

async def send_news_loop():
    while True:
        try:
            stats = load_stats()
            news_items = fetch_new_articles(stats["seen_links"])

            for item in news_items:
                if has_been_sent(item["link"], stats):
                    continue

                text = f"📰 {item['title']}\n\n📝 {item['summary']}"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 مشاهده منبع", url=item["link"])]
                ])

                if item["image"]:
                    await bot.send_photo(
                        chat_id=CHAT_ID,
                        photo=item["image"],
                        caption=text[:1024],  # محدودیت تلگرام
                        reply_markup=buttons
                    )
                else:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=text,
                        reply_markup=buttons
                    )

                mark_as_sent(item["link"], stats)
        except Exception as e:
            print(f"❌ Error: {e}")
        await asyncio.sleep(15)

if __name__ == "__main__":
    print("🚀 ربات خبری کافه شمس در حال اجراست...")
    asyncio.run(send_news_loop())
