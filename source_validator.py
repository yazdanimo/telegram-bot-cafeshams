import requests
from bs4 import BeautifulSoup
import json

def validate_sources(input_file="sources.json", valid_output="sources_valid.json", weak_output="sources_weak.json"):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            sources = json.load(f)
    except Exception as e:
        print(f"❗️ خطا در خواندن فایل {input_file}: {e}")
        return

    valid_sources = []
    weak_sources = []

    print("\n📡 بررسی منابع RSS:\n")

    for source in sources:
        name = source.get("name")
        url = source.get("url")

        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")

            if len(items) >= 5:
                print(f"✅ معتبر و پربار: {name} → خبرها: {len(items)}")
                valid_sources.append(source)
            elif len(items) >= 1:
                print(f"⚠️ سالم ولی کم‌خبر: {name} → فقط {len(items)} خبر")
                weak_sources.append(source)
            else:
                print(f"🚫 بدون خبر: {name}")
        except Exception as e:
            print(f"❌ نامعتبر: {name} → خطا: {e}")

    try:
        with open(valid_output, "w", encoding="utf-8") as f:
            json.dump(valid_sources, f, ensure_ascii=False, indent=2)
        with open(weak_output, "w", encoding="utf-8") as f:
            json.dump(weak_sources, f, ensure_ascii=False, indent=2)
        print(f"\n📁 منابع معتبر ذخیره شدند در: {valid_output}")
        print(f"📁 منابع کم‌خبر ذخیره شدند در: {weak_output}")
    except Exception as e:
        print(f"❗️ خطا در نوشتن فایل خروجی: {e}")

if __name__ == "__main__":
    validate_sources()
