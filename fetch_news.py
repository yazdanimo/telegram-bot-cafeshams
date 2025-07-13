# درون fetch_news.py — اضافه کردن گزارش رد آیتم‌های تکراری یا خراب

SKIPPED_LOG_FILE = "skipped_items.json"

def log_skipped(source, url, reason, title=None):
    try:
        with open(SKIPPED_LOG_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    except:
        items = []
    items.append({
        "source": source,
        "url": url,
        "title": title,
        "reason": reason
    })
    with open(SKIPPED_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

# هنگام بررسی هر آیتم خبر:

for item in items[:3]:
    raw = item.get("link") or ""
    u = normalize_url(raw)
    if not u or u in sent_urls or u in sent_now or u in bad_links:
        log_skipped(name, u, "URL already sent", item.get("title"))
        continue

    try:
        async with session.get(raw) as res:
            if res.status != 200:
                raise Exception(f"HTTP {res.status}")
            html = await res.text()

        full = extract_full_content(html)
        summ = summarize_text(full)

        if is_garbage(full) or is_garbage(summ):
            log_skipped(name, u, "Garbage content", item.get("title"))
            log_garbage(name, raw, item.get("title", ""), full)
            bad_links.add(u)
            continue

        cap = format_news(name, item.get("title", ""), summ, raw)
        h = hashlib.md5(cap.encode("utf-8")).hexdigest()
        if h in sent_hashes or h in hashes_now:
            log_skipped(name, u, "Duplicate hash", item.get("title"))
            continue

        await safe_send(bot, chat_id, cap, parse_mode="HTML")
        sent_now.add(u)
        hashes_now.add(h)
        sent += 1

    except Exception as e:
        log_skipped(name, u, f"Exception: {str(e)}", item.get("title"))
        print("⚠️ خطا در پردازش", raw, "→", e)
        bad_links.add(u)
        err += 1
