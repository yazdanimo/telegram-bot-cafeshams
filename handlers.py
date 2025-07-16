# handlers.py
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

async def send_news_with_button(bot, chat_id: int, text: str):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ارسال به کانال", callback_data="forward_news")]
    ])
    await bot.send_message(chat_id=chat_id, text=text,
                           reply_markup=keyboard, parse_mode="HTML")

async def handle_forward_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = update.callback_query.message.text_html
    channel = int(os.getenv("CHANNEL_ID"))
    await context.bot.send_message(chat_id=channel, text=text, parse_mode="HTML")
    await update.callback_query.edit_message_reply_markup(
        InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال شد", callback_data="done")]])
    )
