import datetime

async def fetch_and_send_news(bot, chat_id, sent_urls, category_filter=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    health_report = {}

    for source in sources:
        name = source.get("name")
        url = source.get("url")
        category = source.get("category", "news")

        if category_filter and category != category_filter:
            continue

        try:
            res = requests.get(url, timeout=10, headers=headers)
            res.raise_for_status()
        except:
            print(f"❌ خطا در RSS {name}")
            dead_sources.add(name)
            health_report[name] = { "total": 0, "success": 0, "failed": 1 }
            continue

        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")
        print(f"\n📡 RSS {name} → {len(items)} خبر")

        failed = 0
        success_count = 0

        for item in items[:8]:
            link = item.link.text.strip() if item.link else ""
            if not link or link in sent_urls:
                continue

            domain = urlparse(link).netloc.lower()
            if any(blocked in domain or blocked in link for blocked in blocked_domains):
                print(f"🚫 لینک مسدود یا محافظت‌شده: {link}")
                failed += 1
                continue

            title = item.title.text.strip() if item.title else "بدون عنوان"
            raw_html = item.description.text.strip() if item.description else ""
            image_url = extract_image_from_html(raw_html)

            if any(x in link.lower() for x in ["/photo/", "/gallery/", "/picture/"]):
                if image_url:
                    msg = f"🖼 گزارش تصویری از {name}\n🎙 {title}\n🆔 @cafeshamss"
                    try:
                        await bot.send_photo(chat_id=chat_id, photo=image_url, caption=msg[:1024])
                        sent_urls.add(link)
                        success_count += 1
                        print(f"📸 ارسال گالری موفق از {name}")
                        await asyncio.sleep(2)
                    except:
                        failed += 1
                else:
                    print(f"⚠️ لینک گالری بدون تصویر معتبر: {link}")
                continue

            full_text, _ = extract_full_content(link)
            if "404" in full_text or not full_text:
                print(f"❌ خطا در دریافت محتوا از: {link}")
                failed += 1
                continue

            if not assess_content_quality(full_text):
                print(f"⚠️ رد شد: متن ضعیف از {name}")
                failed += 1
                continue

            try:
                lang = detect(title + full_text)
                if lang == "en":
                    title = translate_text(title)
                    full_text = translate_text(full_text)
            except:
                pass

            clean_text = clean_incomplete_sentences(full_text)
            intro = extract_intro_paragraph(clean_text)
            short_link = shorten_link(link)

            caption = (
                f"🗞️ خبر ویژه از {name} ({category})\n🎙️ {title}\n\n📝 {intro}\n\n🆔 @cafeshamss ☕️📡🍪"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 مشاهده خبر در منبع", url=short_link)]
            ])

            try:
                if image_url:
                    await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption[:1024], reply_markup=keyboard)
                else:
                    await bot.send_message(chat_id=chat_id, text=caption[:4096], reply_markup=keyboard)
                sent_urls.add(link)
                success_count += 1
                print(f"✅ ارسال موفق از {name}")
                await asyncio.sleep(2)
            except:
                failed += 1

        if failed >= 4:
            weak_sources.add(name)

        health_report[name] = {
            "total": len(items),
            "success": success_count,
            "failed": failed
        }

    # ذخیره فایل گزارش سلامت منابع
    date_key = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        with open("source_health.json", "w", encoding="utf-8") as f:
            json.dump({date_key: health_report}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره source_health.json: {e}")

    print(f"\n📊 مجموع ارسال‌شده‌ها: {len(sent_urls)}")
    if dead_sources:
        print(f"🗑 منابع مرده: {', '.join(dead_sources)}")
    if weak_sources:
        print(f"⚠️ منابع ضعیف: {', '.join(weak_sources)}")
