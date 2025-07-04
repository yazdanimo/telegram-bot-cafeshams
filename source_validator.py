import requests
from bs4 import BeautifulSoup
import json

def validate_sources(input_file="sources.json", output_file="sources_valid.json"):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            sources = json.load(f)
    except Exception as e:
        print(f"❗️ خطا در خواندن فایل {input_file}: {e}")
        return

    valid_sources = []
    print("\n📡 بررسی منابع RSS:\n")

    for source in sources:
        name = source.get("name")
        url = source.get("url")
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")

            if len(items) >= 1:
                print(f"✅ معتبر: {name} → تعداد خبرها: {len(items)}")
                valid_sources.append(source)
            else:
                print(f"⚠️ خالی یا بدون خبر: {name}")
        except Exception as e:
            print(f"❌ نامعتبر: {name} → خطا: {e}")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(valid_sources, f, ensure_ascii=False, indent=2)
        print(f"\n📁 منابع سالم ذخیره شدند در فایل: {output_file}")
    except Exception as e:
        print(f"❗️ خطا در نوشتن فایل خروجی: {e}")

if __name__ == "__main__":
    validate_sources()
