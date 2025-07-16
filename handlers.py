import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002685190359"))

async def send_news_with_button(bot, chat_id: int, text: str):
    logging.info(f"📤 send_news: chat_id={chat_id}, len(text)={len(text)}")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ارسال به کانال", callback_data="forward_news")]
    ])
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def handle_forward_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = update.callback_query.message.text_html
    logging.info(f"📨 forward to channel {CHANNEL_ID}, len(text)={len(text)}")
    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        parse_mode="HTML"
    )
    await update.callback_query.edit_message_reply_markup(
        InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال شد", callback_data="done")]])
    )
