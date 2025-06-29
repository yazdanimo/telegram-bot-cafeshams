import asyncio
import os
from telegram import Bot, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from fetch_news import fetch_news

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002514471809  # گروه سردبیری محمد

bot = Bot(token=BOT_TOKEN)

def format_message(news):
    text = f"🗞 <b>{news['source']}</b>\n\n"
    text += f"<b>{news['title']}</b>\n\n"
    text += f"{news['summary']}\n\n"
    return text.strip()

def build_keyboard(news):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 خواندن کامل خبر", url=news['link'])]
    ])

async def send_news():
    news_list = fetch_news()
    for news in news_list:
        try:
            text = format_message(news)
            keyboard = build_keyboard(news)
            if news["image"]:
                await bot.send_photo(
                    chat_id=GROUP_ID,
                    photo=news["image"],
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_message(
                    chat_id=GROUP_ID,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            await asyncio.sleep(2)  # کمی فاصله برای جلوگیری از بن
        except Exception as e:
            print(f"❌ ارسال ناموفق: {e}")

if __name__ == "__main__":
    asyncio.run(send_news())
