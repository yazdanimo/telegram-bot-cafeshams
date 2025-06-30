import aiohttp
import asyncio
from langdetect import detect

def get_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

async def async_translate(text, target_lang="fa"):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target_lang,
        "dt": "t",
        "q": text,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                result = await response.json()
                return "".join([item[0] for item in result[0]])
            else:
                return text  # اگر ترجمه با خطا مواجه شد، متن اصلی را برگردان

def translate_text(text, dest="fa"):
    return asyncio.run(async_translate(text, target_lang=dest))
