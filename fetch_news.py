import feedparser
import asyncio

async def fetch_and_send_news(sources, bot, group_id):
    for source in sources:
        try:
            url = source.get("url")
            name = source.get("name", "منبع نامشخص")

            if not url:
                continue

            feed = feedparser.parse(url)
            if not feed.entries:
                continue

            entry = feed.entries[0]
            title = entry.get("title", "بدون عنوان")
            link = entry.get("link", "")

            message = f"📰 <b>{name}</b>\n<b>{title}</b>\n{link}"
            await bot.send_message(chat_id=group_id, text=message, parse_mode="HTML")

            await asyncio.sleep(1)  # کنترل سرعت ارسال برای جلوگیری از Flood

        except Exception as e:
            print(f"❗️خطا در منبع {source.get('name')}: {e}")
