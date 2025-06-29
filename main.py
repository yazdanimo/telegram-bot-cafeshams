import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

print("📡 ربات برای دریافت Chat ID اجرا شد...")

async def echo_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    print(f"📦 Chat ID: {chat.id}, Type: {chat.type}")
    await update.message.reply_text(f"Chat ID: {chat.id}\nType: {chat.type}")

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    domain = os.getenv("WEBHOOK_DOMAIN")
    port = int(os.environ.get("PORT", 8443))

    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.ALL, echo_id))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"https://{domain}/"
    )
