# ساخت جدول نهایی گزارش در fetch_news.py

hdr = ["منبع", "دریافت", "ارسال", "خطا"]
widths = {h: len(h) for h in hdr}

# تنظیم عرض ستون‌ها بر اساس محتویات واقعی
max_source_len = max(len(r["منبع"]) for r in stats)
widths["منبع"] = max(widths["منبع"], max_source_len)

for r in stats:
    for h in hdr:
        widths[h] = max(widths[h], len(str(r[h])))

lines = [
    "📊 گزارش دریافت اخبار:\n",
    "  ".join(f"{h:<{widths[h]}}" for h in hdr),
    "  ".join("-" * widths[h] for h in hdr)
]

for r in stats:
    lines.append(
        "  ".join(
            f"{r[h]:<{widths[h]}}" if h == "منبع"
            else f"{r[h]:>{widths[h]}}"
            for h in hdr
        )
    )

report = "<pre>" + "\n".join(lines) + "</pre>"
await safe_send(bot, chat_id, report, parse_mode="HTML")
