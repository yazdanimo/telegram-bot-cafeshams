import asyncio, os, feedparser, aiohttp
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from telegram.request import HTTPXRequest
from utils import fetch_url, extract_news_title_image_text
from news_sources import news_sources

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
EDITOR_GROUP_ID = int(os.getenv("EDITOR_GROUP_ID"))
SENT_LINKS = set()

# پاسخ به /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! 👋\nربات خبری کافه شمس فعال است ✅")

# ارسال خودکار اخبار
async def send_news(context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        for source in news_sources:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:5]:
                link = entry.link
                if link in SENT_LINKS:
                    continue

                html = await fetch_url(session, link)
                title, image_url, text = await extract_news_title_image_text(html, source["name"], link)
                caption = f"{title}\n\n📝 {text}" if text else title
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📎 مشاهده خبر", url=link)]])

                try:
                    if image_url:
                        try:
                            async with session.get(image_url, timeout=5) as img_response:
                                if img_response.status == 200:
                                    await context.bot.send_photo(
                                        chat_id=EDITOR_GROUP_ID,
                                        photo=image_url,
                                        caption=caption,
                                        reply_markup=keyboard
                                    )
                                else:
                                    print(f"⚠️ عکس بارگذاری نشد ({img_response.status})")
                                    await context.bot.send_message(
                                        chat_id=EDITOR_GROUP_ID,
                                        text=caption,
                                        reply_markup=keyboard
                                    )
                        except Exception as e:
                            print(f"⚠️ خطا در دریافت عکس: {e}")
                            await context.bot.send_message(
                                chat_id=EDITOR_GROUP_ID,
                                text=caption,
                                reply_markup=keyboard
                            )
                    else:
                        await context.bot.send_message(
                            chat_id=EDITOR_GROUP_ID,
                            text=caption,
                            reply_markup=keyboard
                        )

                    print(f"✅ خبر ارسال شد: {title}")
                except Exception as e:
                    print(f"⛔️ خطا در ارسال به تلگرام: {e}")

                SENT_LINKS.add(link)

# اجرای اصلی
async def main():
    request = HTTPXRequest(read_timeout=20, write_timeout=20, connect_timeout=10)
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))

    job_queue = JobQueue()
    job_queue.set_application(app)
    job_queue.run_repeating(send_news, interval=15, first=5)

    await app.initialize()
    await app.start()
    await job_queue.start()
    print("✅ ربات خبری کافه شمس آماده است!")

if __name__ == "__main__":
    asyncio.run(main())
