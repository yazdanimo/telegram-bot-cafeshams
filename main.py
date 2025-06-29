import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("ربات خبری کافه شمس آماده است!")

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    port = int(os.environ.get("PORT", 8443))
    domain = os.getenv("WEBHOOK_DOMAIN")  # مثل telegram-bot-cafeshams.up.railway.app

    webhook_url = f"https://{domain}/{token}"

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url
    )
