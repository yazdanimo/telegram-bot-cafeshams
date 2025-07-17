#!/usr/bin/env python3
"""
تست ساده برای تشخیص مشکل Connection Pool
این فایل رو در Railway اجرا کن تا ببینیم کجا مشکل هست
"""

import asyncio
import os
import logging
from telegram import Bot
from telegram.request import HTTPXRequest

# تنظیم logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# اطلاعات ربات
BOT_TOKEN = os.getenv("BOT_TOKEN", "7957685811:AAG_gzimHewoCWteEIf0mOcLDAnMgOu6Z3M")
CHAT_ID = -1002514471809

async def test_simple_send():
    """تست ساده ارسال پیام"""
    print("🔧 شروع تست ساده ارسال پیام...")
    
    # ساخت request handler با تنظیمات محافظه‌کارانه
    request = HTTPXRequest(
        connection_pool_size=5,      # کم شروع می‌کنیم
        pool_timeout=30.0,
        read_timeout=60.0,
        write_timeout=60.0,
        connect_timeout=30.0,
        http_version='1.1'
    )
    
    # ساخت bot
    bot = Bot(token=BOT_TOKEN, request=request)
    
    try:
        # تست شماره 1: دریافت اطلاعات bot
        print("📋 تست 1: دریافت اطلاعات ربات...")
        me = await bot.get_me()
        print(f"✅ ربات شناخته شد: {me.first_name}")
        
        # تست شماره 2: ارسال پیام ساده
        print("📤 تست 2: ارسال پیام ساده...")
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text="🧪 تست اتصال - اگر این پیام رو می‌بینی، connection pool کار می‌کنه!"
        )
        print(f"✅ پیام ارسال شد: {message.message_id}")
        
        # تست شماره 3: ارسال چندین پیام متوالی
        print("📤 تست 3: ارسال ۳ پیام متوالی...")
        for i in range(3):
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"🔢 پیام شماره {i+1} - تست Connection Pool"
            )
            print(f"✅ پیام {i+1} ارسال شد")
            await asyncio.sleep(2)  # فاصله بین پیام‌ها
        
        print("🎉 همه تست‌ها موفق بودن! Connection Pool درست کار می‌کنه.")
        
    except Exception as e:
        print(f"❌ خطا در تست: {e}")
        print(f"❌ نوع خطا: {type(e)}")
        import traceback
        print(f"❌ جزئیات: {traceback.format_exc()}")
    
    finally:
        # تمیز کردن
        try:
            await bot.shutdown()
            print("🧹 Bot shutdown شد")
        except:
            pass

async def test_concurrent_sends():
    """تست ارسال همزمان چندین پیام"""
    print("🔧 شروع تست ارسال همزمان...")
    
    request = HTTPXRequest(
        connection_pool_size=10,
        pool_timeout=60.0,
        read_timeout=90.0,
        write_timeout=90.0,
        connect_timeout=45.0,
        http_version='1.1'
    )
    
    bot = Bot(token=BOT_TOKEN, request=request)
    
    try:
        # ساخت لیست task ها
        tasks = []
        for i in range(5):  # ۵ پیام همزمان
            task = bot.send_message(
                chat_id=CHAT_ID,
                text=f"🚀 پیام همزمان شماره {i+1}"
            )
            tasks.append(task)
        
        # اجرای همزمان
        print("🚀 اجرای ۵ پیام همزمان...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # بررسی نتایج
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ پیام {i+1} ناموفق: {result}")
            else:
                print(f"✅ پیام {i+1} موفق: {result.message_id}")
                success_count += 1
        
        print(f"📊 نتیجه: {success_count}/5 پیام موفق")
        
    except Exception as e:
        print(f"❌ خطا در تست همزمان: {e}")
    
    finally:
        try:
            await bot.shutdown()
        except:
            pass

if __name__ == "__main__":
    print("🎯 شروع تست‌های Connection Pool")
    print("=" * 50)
    
    # اجرای تست‌ها
    asyncio.run(test_simple_send())
    print("-" * 50)
    asyncio.run(test_concurrent_sends())
    
    print("=" * 50)
    print("🏁 تست‌ها تمام شد")
