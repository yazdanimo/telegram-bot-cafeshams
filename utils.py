from deep_translator import GoogleTranslator
from langdetect import detect
import logging

async def async_translate(text, target_lang='en'):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        logging.error(f"❗️ خطا در ترجمه: {e}")
        return text

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def translate_text(text, dest="fa"):
    lang = detect_language(text)
    
    if lang == "fa" or lang == "en":
        return text  # No translation needed
    
    if dest == "en":
        return GoogleTranslator(source=lang, target="en").translate(text)
    else:
        # Translate to English first, then to Persian
        intermediate = GoogleTranslator(source=lang, target="en").translate(text)
        return GoogleTranslator(source="en", target="fa").translate(intermediate)
