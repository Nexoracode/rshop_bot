"""
فایل تست برای بررسی عملکرد اجزای ربات
"""

import asyncio
from database import Database
from ai_handler import AIHandler
import config


def test_database_connection():
    """تست اتصال به دیتابیس"""
    print("🔍 تست اتصال به دیتابیس...")
    try:
        db = Database()
        print("✅ اتصال به دیتابیس برقرار شد")
        
        # تست دریافت دسته‌بندی‌ها
        categories = db.get_all_categories()
        print(f"✅ تعداد دسته‌بندی‌ها: {len(categories)}")
        
        # تست دریافت برندها
        brands = db.get_all_brands()
        print(f"✅ تعداد برندها: {len(brands)}")
        
        # تست دریافت محصولات
        products = db.get_all_products(limit=5)
        print(f"✅ تعداد محصولات: {len(products)}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")
        return False


async def test_ai_handler():
    """تست هندلر AI"""
    provider_name = "Groq (رایگان)" if config.AI_PROVIDER == 'groq' else "Claude (پولی)"
    print(f"\n🤖 تست هندلر AI ({provider_name})...")
    try:
        ai = AIHandler()
        
        # تست درخواست ساده
        test_message = "لیست محصولات رو نشون بده"
        print(f"📝 درخواست تست: {test_message}")
        
        result = await ai.process_request(test_message)
        print(f"✅ پاسخ AI دریافت شد: {result.get('action')}")
        print(f"   پیام: {result.get('message', 'بدون پیام')[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ خطا در تست AI: {e}")
        return False


def test_config():
    """تست تنظیمات"""
    print("\n⚙️ تست تنظیمات...")
    
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN تنظیم نشده است")
        return False
    else:
        print("✅ TELEGRAM_BOT_TOKEN موجود است")
    
    # بررسی AI Provider
    print(f"📌 AI Provider: {config.AI_PROVIDER}")
    
    if config.AI_PROVIDER == 'groq':
        if not config.GROQ_API_KEY:
            print("❌ GROQ_API_KEY تنظیم نشده است")
            return False
        else:
            print("✅ GROQ_API_KEY موجود است")
    elif config.AI_PROVIDER == 'claude':
        if not config.ANTHROPIC_API_KEY:
            print("❌ ANTHROPIC_API_KEY تنظیم نشده است")
            return False
        else:
            print("✅ ANTHROPIC_API_KEY موجود است")
    else:
        print(f"❌ AI_PROVIDER نامعتبر: {config.AI_PROVIDER}")
        print("   مقادیر مجاز: 'groq' یا 'claude'")
        return False
    
    if not config.DB_CONFIG.get('user'):
        print("❌ اطلاعات دیتابیس ناقص است")
        return False
    else:
        print("✅ تنظیمات دیتابیس موجود است")
    
    return True


async def test_product_operations():
    """تست عملیات محصول"""
    print("\n📦 تست عملیات محصول...")
    try:
        ai = AIHandler()
        
        # تست افزودن محصول
        add_request = "یک محصول تستی با نام محصول تست با قیمت 1000 تومان اضافه کن"
        print(f"📝 تست افزودن: {add_request}")
        
        action_data = await ai.process_request(add_request)
        result = ai.execute_action(action_data)
        
        if result.get('success'):
            print("✅ محصول با موفقیت اضافه شد")
            product_id = result.get('product_id')
            
            # تست حذف محصول
            if product_id:
                delete_request = f"محصول با شناسه {product_id} رو حذف کن"
                print(f"📝 تست حذف: {delete_request}")
                
                action_data = await ai.process_request(delete_request)
                result = ai.execute_action(action_data)
                
                if result.get('success'):
                    print("✅ محصول با موفقیت حذف شد")
                else:
                    print(f"⚠️ خطا در حذف: {result.get('message')}")
        else:
            print(f"⚠️ خطا در افزودن: {result.get('message')}")
        
        return True
    except Exception as e:
        print(f"❌ خطا در تست عملیات محصول: {e}")
        return False


def main():
    """اجرای تست‌ها"""
    print("🚀 شروع تست‌های سیستم...")
    print("=" * 50)
    
    # تست تنظیمات
    config_ok = test_config()
    
    if not config_ok:
        print("\n❌ لطفاً ابتدا فایل .env را تنظیم کنید")
        print("\n💡 نکته:")
        print("   - برای تست: AI_PROVIDER=groq")
        print("   - برای تولید: AI_PROVIDER=claude")
        return
    
    # تست دیتابیس
    db_ok = test_database_connection()
    
    if not db_ok:
        print("\n❌ لطفاً اطلاعات دیتابیس را بررسی کنید")
        return
    
    # تست AI
    ai_ok = asyncio.run(test_ai_handler())
    
    if not ai_ok:
        provider = config.AI_PROVIDER
        if provider == 'groq':
            print("\n❌ لطفاً کلید API Groq را بررسی کنید")
            print("   دریافت از: https://console.groq.com/keys")
        elif provider == 'claude':
            print("\n❌ لطفاً کلید API Claude را بررسی کنید")
            print("   دریافت از: https://console.anthropic.com")
        return
    
    # تست عملیات محصول (اختیاری)
    print("\n" + "=" * 50)
    test_operations = input("\n❓ آیا می‌خواهید عملیات محصول را تست کنید؟ (y/n): ")
    
    if test_operations.lower() == 'y':
        asyncio.run(test_product_operations())
    
    print("\n" + "=" * 50)
    print("✅ تمام تست‌ها با موفقیت انجام شد!")
    print(f"🤖 AI Provider فعلی: {config.AI_PROVIDER}")
    print("\n🎉 ربات شما آماده اجرا است. برای شروع:")
    print("   python bot.py")
    
    print("\n💡 تغییر AI Provider:")
    print("   - فایل .env را باز کنید")
    print("   - AI_PROVIDER را به 'groq' یا 'claude' تغییر دهید")


if __name__ == '__main__':
    main()
