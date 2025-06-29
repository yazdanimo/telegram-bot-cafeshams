# main.py
import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from fetch_news import fetch_new_articles

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("\u274c BOT_TOKEN environment variable not set!")
if not CHAT_ID:
    raise ValueError("\u274c CHAT_ID environment variable not set!")

async def start(update, context):
    await update.message.reply_text("\u2705 \u0631\u0628\u0627\u062a \u062e\u0628\u0631\u06cc \u06a9\u0627\u0641\u0647 \u0634\u0645\u0633 \u0622\u0645\u0627\u062f\u0647 \u0627\u0633\u062a!")

async def news_job(context):
    articles = await fetch_new_articles()
    for article in articles:
        try:
            await context.bot.send_photo(
                chat_id=CHAT_ID,
                photo=article["image"],
                caption=f"\u2705 \u062e\u0628\u0631 \u0627\u0631\u0633\u0627\u0644 \u0634\u062f: {article['source']} | {article['title']}\n\n{article['summary']}",
                parse_mode="HTML"
            )
        except Exception as e:
            print("Error sending message:", e)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(news_job, interval=15, first=5)
    print("\u2705 Token loaded successfully (starts with):", BOT_TOKEN[:10], "...")
    print("\ud83d\udce1 \u0634\u0631\u0648\u0639 \u0627\u062c\u0631\u0627\u06cc \u0628\u0631\u0646\u0627\u0645\u0647...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
