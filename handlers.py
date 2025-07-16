# handlers.py
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

async def send_news_with_button(bot, chat_id, news_text: str):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ارسال خبر به کانال", callback_data="forward_news")]
    ])
    await bot.send_message(chat_id=chat_id, text=news_text,
                           reply_markup=keyboard, parse_mode="HTML")

async def handle_forward_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    news_text = query.message.text
    channel_id = int(os.getenv("CHANNEL_ID"))
    await context.bot.send_message(chat_id=channel_id,
                                   text=news_text, parse_mode="HTML")
    await query.edit_message_reply_markup(
        InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 ارسال شد به کانال", callback_data="done")]
        ])
    )
