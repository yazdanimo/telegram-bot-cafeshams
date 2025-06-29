import asyncio
import json
import os
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fetch_news import fetch_news

TOKEN = os.getenv("BOT_TOKEN") or "7957685811:AAGC3ruFWuHouVsbsPt6TiPSv15CTduoyxA"
GROUP_ID = -1002514471809  # گروه سردبیری

app = ApplicationBuilder().token(TOKEN).build()
scheduler = AsyncIOScheduler()

sent_titles = set()

async def send_news(context: ContextTypes.DEFAULT_TYPE):
    global sent_titles
    try:
        news_list = fetch_news()
        for news in news_list:
            if news['title'] in sent_titles:
                continue
            sent_titles.add(news['title'])

            message = f"<b>{news['source']}</b> | {news['title']}"
            if news.get("summary"):
                message += f"\n\n{news['summary']}"

            await app.bot.send_message(
                chat_id=GROUP_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
    except Exception as e:
        print(f"خطا در ارسال خبر: {e}")

@app.on_startup
async def startup(_: ContextTypes.DEFAULT_TYPE) -> None:
    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    scheduler.add_job(send_news, "interval", minutes=1, next_run_time=None)
    scheduler.start()

if __name__ == '__main__':
    async def send_test_message():
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=GROUP_ID, text="🧪 تست ارسال دستی")

    asyncio.run(send_test_message())
    app.run_polling()
