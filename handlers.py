import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils import safe_send

CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002685190359"))

async def send_news_with_button(bot, chat_id: int, text: str):
    try:
        logging.info(f"📤 send_news to {chat_id}, len={len(text)}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ ارسال به کانال", callback_data="forward_news")]
        ])
        await safe_send(
            bot,
            chat_id,
            text,
            reply_markup=keyboard,
            parse_mode=None
        )
    except Exception as e:
        logging.error(f"Error sending news with button: {e}")

async def handle_forward_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
        txt = update.callback_query.message.text
        
        logging.info(f"📨 forward to CHANNEL_ID={CHANNEL_ID}, len={len(txt)}")
        
        await safe_send(
            context.bot,
            CHANNEL_ID,
            txt,
            parse_mode=None
        )
        
        await update.callback_query.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال شد", callback_data="done")]])
        )
        
    except Exception as e:
        logging.error(f"Error handling forward news: {e}")
        try:
            await update.callback_query.answer("خطا در ارسال!")
        except:
            pass
