# main.py
import asyncio
from telegram.ext import ApplicationBuilder
from fetch_news import fetch_and_send_news
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    async def job():
        while True:
            await fetch_and_send_news()
            await asyncio.sleep(60)  # هر 1 دقیقه

    asyncio.create_task(job())
    print("✅ ربات در حال اجراست و هر 1 دقیقه چک می‌کند...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())


# fetch_news.py
import json
import aiohttp
import feedparser
from utils import is_duplicate, summarize_text, translate_if_needed, send_news_to_channel

with open("sources.json", encoding="utf-8") as f:
    SOURCES = json.load(f)

SEEN_URLS = set()

async def fetch_rss(session, url):
    try:
        async with session.get(url, timeout=10) as resp:
            data = await resp.text()
            return feedparser.parse(data)
    except Exception:
        return None

async def fetch_all_rss():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_rss(session, src["url"]) for src in SOURCES if src["type"] == "rss"]
        return await asyncio.gather(*tasks)

async def fetch_and_send_news():
    feeds = await fetch_all_rss()
    for i, feed in enumerate(feeds):
        if not feed or not feed.entries:
            continue

        source = SOURCES[i]["name"]
        for entry in feed.entries[:3]:
            url = entry.link
            if url in SEEN_URLS or is_duplicate(url):
                continue

            SEEN_URLS.add(url)
            title = entry.title
            description = entry.get("summary", "")

            text = f"{title}\n\n{description}"
            text = await translate_if_needed(text)
            summary = summarize_text(text)
            caption = f"📰 {source}\n\n{summary}\n\n🔗 {url}"
            await send_news_to_channel(caption, preview=url)
import os
print("🗂 موجودی پوشه:", os.listdir("."))
