import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

print("🔄 شروع اجرای برنامه...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات خبری کافه شمس آماده است!")

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    port = int(os.environ.get("PORT", 8443))
    domain = os.getenv("WEBHOOK_DOMAIN")

    webhook_url = f"https://{domain}/"

    print(f"📡 در حال راه‌اندازی webhook روی: {webhook_url}")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url
    )
