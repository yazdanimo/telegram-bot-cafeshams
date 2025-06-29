import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("✅ ربات خبری کافه شمس آماده است!")

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("❌ BOT_TOKEN environment variable not set!")

    print(f"✅ Token loaded successfully (starts with): {token[:10]}...")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    print("📡 شروع اجرای برنامه...")

    # اگر webhook استفاده نمی‌کنی، از polling استفاده کن:
    app.run_polling()

    # اگر webhook استفاده می‌کنی، اینو فعال کن و بالا رو غیرفعال کن:
    # import asyncio
    # port = int(os.environ.get("PORT", "8443"))
    # webhook_url = os.environ.get("WEBHOOK_DOMAIN", "") + "/webhook"
    # app.run_webhook(
    #     listen="0.0.0.0",
    #     port=port,
    #     webhook_url=webhook_url,
    # )
