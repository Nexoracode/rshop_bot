import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# AI Provider Selection: 'groq' or 'claude'
AI_PROVIDER = os.getenv('AI_PROVIDER', 'groq')  # Default: groq (رایگان)

# Groq API Configuration (رایگان)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = "llama-3.3-70b-versatile"

# Claude API Configuration (پولی)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'ecommerce'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# FTP Configuration for Image Upload
FTP_CONFIG = {
    'host': os.getenv('FTP_HOST', 'dl.poshtybanman.ir'),
    'port': int(os.getenv('FTP_PORT', 21)),
    'user': os.getenv('FTP_USER'),
    'password': os.getenv('FTP_PASSWORD'),
    'base_path': os.getenv('FTP_BASE_PATH', '/Rshop/product/'),
    'base_url': os.getenv('FTP_BASE_URL', 'https://dl.poshtybanman.ir/Rshop/product/')
}

# Admin Users (comma-separated user IDs)
ADMIN_USER_IDS = [int(uid.strip()) for uid in os.getenv('ADMIN_USER_IDS', '').split(',') if uid.strip()]

# Bot Settings
BOT_SETTINGS = {
    'max_images_per_product': 10,  # حداکثر تعداد عکس برای محصول
    'max_images_per_category': 1,  # حداکثر تعداد عکس برای دسته‌بندی
    'temp_image_path': '/tmp',  # مسیر ذخیره موقت عکس‌ها
    'default_media_type': 'product',  # نوع پیش‌فرض: product یا category
}

# Bot Messages
MESSAGES = {
    'welcome': """
سلام! 👋
من ربات مدیریت فروشگاه شما هستم.

می‌توانید به زبان ساده با من صحبت کنید و من:
✅ محصولات جدید اضافه می‌کنم
✅ دسته‌بندی‌ها را مدیریت می‌کنم
✅ برندها را اضافه/ویرایش می‌کنم
✅ ویژگی‌های محصولات را تنظیم می‌کنم
✅ لیست محصولات را نمایش می‌دهم
📸 تصاویر محصولات و دسته‌بندی‌ها را آپلود می‌کنم

📸 نحوه آپلود عکس:

🔹 محصول (چند عکس):
/setproduct
[عکس 1، 2، 3...]
"محصول گوشی سامسونگ با قیمت 15000000 تومان"

🔹 دسته‌بندی (یک عکس):
/setcategory
[یک عکس]
"دسته‌بندی موبایل اضافه کن"

🤖 AI Provider: {provider}
📊 حداکثر عکس محصول: {max_product_images}
📂 حداکثر عکس دسته‌بندی: {max_category_images}
    """.format(
        provider="Groq (رایگان)" if AI_PROVIDER == 'groq' else "Claude (پولی)",
        max_product_images=BOT_SETTINGS['max_images_per_product'],
        max_category_images=BOT_SETTINGS['max_images_per_category']
    ),
    
    'unauthorized': '🚫 شما دسترسی به این ربات را ندارید.',
    
    'error': '❌ متأسفانه خطایی رخ داد. لطفاً دوباره امتحان کنید.',
    
    'processing': '⏳ در حال پردازش درخواست شما...',
    
    'success': '✅ عملیات با موفقیت انجام شد!',
    
    'image_uploading': '📸 در حال آپلود تصویر...',
    
    'image_uploaded_product': """
✅ تصویر {count} آپلود شد!
🆔 Media ID: {media_id}
{pinned_text}
📊 مجموع عکس‌ها: {total}
🔗 {url}

💡 {hint}
    """,
    
    'image_uploaded_category': """
✅ تصویر برای دسته‌بندی آپلود شد!
🆔 Media ID: {media_id}
📂 این عکس برای دسته‌بندی است
🔗 {url}

💡 اطلاعات دسته‌بندی رو بنویس
    """,
    
    'image_limit_product': '⚠️ حداکثر {max} عکس برای هر محصول مجازه!\nاگه میخوای عکس‌ها رو تغییر بدی، /clearimages بزن',
    
    'image_limit_category': '⚠️ دسته‌بندی فقط می‌تونه یک عکس داشته باشه!\nاگه میخوای عکس رو تغییر بدی، /clearimages بزن',
    
    'images_cleared': '🗑 {count} عکس آپلود شده پاک شد.\nمی‌تونی دوباره عکس‌های جدید بفرستی.',
    
    'no_images': 'هیچ عکسی آپلود نشده!',
    
    'mode_product': '📦 حالت: محصول\nعکس‌های بعدی برای محصول هستند (تا {max} عکس)',
    
    'mode_category': '📂 حالت: دسته‌بندی\nعکس بعدی برای دسته‌بندی است (فقط یک عکس)',
    
    'ftp_error': '❌ خطا در آپلود به سرور: {error}',
    
    'database_error': '❌ خطا در دیتابیس: {error}',
    
    'ai_error': '❌ خطا در پردازش هوشمند: {error}',
}

# Error Messages
ERROR_MESSAGES = {
    'no_bot_token': 'TELEGRAM_BOT_TOKEN تنظیم نشده است',
    'no_ai_key': 'کلید API هوش مصنوعی تنظیم نشده است',
    'no_db_config': 'اطلاعات دیتابیس ناقص است',
    'no_ftp_config': 'اطلاعات FTP ناقص است',
    'invalid_ai_provider': 'AI_PROVIDER باید groq یا claude باشه',
    'ftp_upload_failed': 'آپلود به FTP ناموفق بود',
    'db_connection_failed': 'اتصال به دیتابیس ناموفق بود',
}

# Validation
def validate_config():
    """بررسی صحت تنظیمات"""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append(ERROR_MESSAGES['no_bot_token'])
    
    if AI_PROVIDER == 'groq' and not GROQ_API_KEY:
        errors.append(ERROR_MESSAGES['no_ai_key'] + ' (Groq)')
    elif AI_PROVIDER == 'claude' and not ANTHROPIC_API_KEY:
        errors.append(ERROR_MESSAGES['no_ai_key'] + ' (Claude)')
    elif AI_PROVIDER not in ['groq', 'claude']:
        errors.append(ERROR_MESSAGES['invalid_ai_provider'])
    
    if not DB_CONFIG.get('user') or not DB_CONFIG.get('password'):
        errors.append(ERROR_MESSAGES['no_db_config'])
    
    if not FTP_CONFIG.get('user') or not FTP_CONFIG.get('password'):
        errors.append(ERROR_MESSAGES['no_ftp_config'])
    
    return errors

# Auto-validate on import
_config_errors = validate_config()
if _config_errors:
    print("⚠️ خطاهای تنظیمات:")
    for error in _config_errors:
        print(f"  - {error}")
    print("\nلطفاً فایل .env را بررسی کنید!")
