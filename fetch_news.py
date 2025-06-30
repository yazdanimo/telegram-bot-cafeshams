import feedparser

async def fetch_and_send_news(sources, bot, group_id):
    for source in sources:
        try:
            url = source.get("url")
            name = source.get("name", "منبع نامشخص")
            feed = feedparser.parse(url)

            if not feed.entries:
                continue

            entry = feed.entries[0]
            title = entry.get("title", "بدون عنوان")
            link = entry.get("link", "")
            message = f"{name} | {title}\n{link}"

            await bot.send_message(chat_id=group_id, text=message)

        except Exception as e:
            print(f"❗️خطا در منبع {source.get('name')}: {e}")
