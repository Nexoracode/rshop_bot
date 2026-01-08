import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import config
from ai_handler import AIHandler
from image_handler import ImageHandler

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ShopBot:
    def __init__(self):
        self.ai_handler = AIHandler()
        self.image_handler = ImageHandler()
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        self._register_handlers()
        
        # ذخیره‌سازی موقت media_ids برای هر کاربر
        # {user_id: {'ids': [media_id1, media_id2, ...], 'type': 'product'/'category'}}
        self.user_media = {}

    def _register_handlers(self):
        """ثبت هندلرهای بات"""
        # دستورات
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("products", self.products_command))
        self.application.add_handler(CommandHandler("categories", self.categories_command))
        self.application.add_handler(CommandHandler("brands", self.brands_command))
        self.application.add_handler(CommandHandler("clearimages", self.clear_images_command))
        self.application.add_handler(CommandHandler("setproduct", self.set_product_type_command))
        self.application.add_handler(CommandHandler("setcategory", self.set_category_type_command))
        
        # دریافت عکس
        self.application.add_handler(
            MessageHandler(filters.PHOTO, self.handle_photo)
        )
        
        # پیام‌های متنی
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        await update.message.reply_text(config.MESSAGES['welcome'])

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /help"""
        help_text = """
🤖 راهنمای استفاده از ربات

📝 دستورات اصلی:
/start - شروع کار با ربات
/help - نمایش این راهنما
/products - لیست محصولات
/categories - لیست دسته‌بندی‌ها
/brands - لیست برندها
/clearimages - پاک کردن عکس‌های آپلود شده
/setproduct - حالت محصول (چند عکسی)
/setcategory - حالت دسته‌بندی (یک عکس)

💬 نحوه استفاده:
فقط کافیست به زبان ساده درخواست خود را بنویسید!

📸 آپلود تصویر:

🔹 برای محصول (چند عکس):
/setproduct
[ارسال عکس 1] ⭐ عکس اصلی
[ارسال عکس 2، 3، ...]
"محصول گوشی سامسونگ A54 با قیمت 15000000 تومان"

🔹 برای دسته‌بندی (یک عکس):
/setcategory
[ارسال عکس]
"دسته‌بندی موبایل اضافه کن"

✨ مثال‌های کاربردی:

📦 محصول با تصویر:
/setproduct
[عکس 1، عکس 2، عکس 3]
"محصول گوشی سامسونگ با قیمت 15000000 تومان"

📂 دسته‌بندی با تصویر:
/setcategory
[یک عکس]
"دسته‌بندی لوازم جانبی اضافه کن"

📦 بدون تصویر:
"یک محصول لپ‌تاپ ایسوس با قیمت 20000000 تومان اضافه کن"

🔍 جستجو و مدیریت:
• "لیست محصولات"
• "موجودی گوشی آیفون 13 رو به 10 تا تغییر بده"

⚡️ نکات:
- پیش‌فرض: حالت محصول (چند عکسی)
- دسته‌بندی: فقط یک عکس
- اشتباهی عکس فرستادی؟ /clearimages
        """
        await update.message.reply_text(help_text)

    async def clear_images_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن عکس‌های آپلود شده"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        if user_id in self.user_media:
            count = len(self.user_media[user_id]['ids'])
            del self.user_media[user_id]
            await update.message.reply_text(
                config.MESSAGES['images_cleared'].format(count=count)
            )
        else:
            await update.message.reply_text(config.MESSAGES['no_images'])
    
    async def set_product_type_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم حالت محصول برای عکس‌ها"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        if user_id not in self.user_media:
            self.user_media[user_id] = {'ids': [], 'type': 'product'}
        else:
            self.user_media[user_id]['type'] = 'product'
        
        await update.message.reply_text(
            config.MESSAGES['mode_product'].format(max=config.BOT_SETTINGS['max_images_per_product'])
        )
    
    async def set_category_type_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم حالت دسته‌بندی برای عکس‌ها"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        if user_id not in self.user_media:
            self.user_media[user_id] = {'ids': [], 'type': 'category'}
        else:
            self.user_media[user_id]['type'] = 'category'
        
        await update.message.reply_text(config.MESSAGES['mode_category'])

    async def products_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /products - نمایش لیست محصولات"""
        if not self._is_authorized(update.effective_user.id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        await update.message.reply_text(config.MESSAGES['processing'])
        
        action_data = {'action': 'list_products'}
        result = self.ai_handler.execute_action(action_data)
        
        await update.message.reply_text(result['message'])

    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /categories - نمایش لیست دسته‌بندی‌ها"""
        if not self._is_authorized(update.effective_user.id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        action_data = {'action': 'list_categories'}
        result = self.ai_handler.execute_action(action_data)
        
        await update.message.reply_text(result['message'])

    async def brands_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /brands - نمایش لیست برندها"""
        if not self._is_authorized(update.effective_user.id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        action_data = {'action': 'list_brands'}
        result = self.ai_handler.execute_action(action_data)
        
        await update.message.reply_text(result['message'])

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش عکس‌های ارسالی"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        processing_msg = await update.message.reply_text(config.MESSAGES['image_uploading'])
        
        try:
            # دانلود عکس از تلگرام
            photo = update.message.photo[-1]  # بزرگترین سایز
            file = await context.bot.get_file(photo.file_id)
            
            # ذخیره موقت
            import time
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), f'telegram_image_{user_id}_{int(time.time())}.jpg')
            await file.download_to_drive(temp_path)
            
            # آپلود به FTP
            result = await self.image_handler.upload_image(temp_path)
            
            # حذف فایل موقت
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if result['success']:
                # اگه لیست media برای این کاربر نداریم، بساز
                if user_id not in self.user_media:
                    self.user_media[user_id] = {'ids': [], 'type': 'product'}  # پیش‌فرض: محصول
                
                media_type = self.user_media[user_id]['type']
                
                # اگه دسته‌بندی و قبلاً عکس آپلود شده، اجازه نده
                if media_type == 'category' and len(self.user_media[user_id]['ids']) >= config.BOT_SETTINGS['max_images_per_category']:
                    await processing_msg.delete()
                    await update.message.reply_text(config.MESSAGES['image_limit_category'])
                    return
                
                # اگه محصول و بیش از حد مجاز عکس آپلود شده
                if media_type == 'product' and len(self.user_media[user_id]['ids']) >= config.BOT_SETTINGS['max_images_per_product']:
                    await processing_msg.delete()
                    await update.message.reply_text(
                        config.MESSAGES['image_limit_product'].format(max=config.BOT_SETTINGS['max_images_per_product'])
                    )
                    return
                
                # اضافه کردن media_id به لیست
                self.user_media[user_id]['ids'].append(result['media_id'])
                
                image_count = len(self.user_media[user_id]['ids'])
                is_first = image_count == 1
                
                await processing_msg.delete()
                
                if media_type == 'product':
                    pinned_text = "⭐ این عکس اصلی محصول میشه" if is_first else ""
                    hint = "عکس دیگه هم داری بفرست یا اطلاعات محصول رو بنویس"
                    
                    message = config.MESSAGES['image_uploaded_product'].format(
                        count=image_count,
                        media_id=result['media_id'],
                        pinned_text=pinned_text,
                        total=image_count,
                        url=result['url'],
                        hint=hint
                    )
                else:  # category
                    message = config.MESSAGES['image_uploaded_category'].format(
                        media_id=result['media_id'],
                        url=result['url']
                    )
                
                await update.message.reply_text(message)
            else:
                await processing_msg.delete()
                await update.message.reply_text(
                    config.MESSAGES['ftp_error'].format(error=result.get('error'))
                )
                
        except Exception as e:
            logger.error(f"خطا در پردازش عکس: {e}")
            await processing_msg.delete()
            await update.message.reply_text(
                config.MESSAGES['ai_error'].format(error=str(e))
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش پیام‌های متنی کاربر"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text(config.MESSAGES['unauthorized'])
            return
        
        user_message = update.message.text
        logger.info(f"پیام از کاربر {user_id}: {user_message}")
        
        # نمایش پیام در حال پردازش
        processing_msg = await update.message.reply_text(config.MESSAGES['processing'])
        
        try:
            # بررسی آیا کاربر قبلاً عکس‌هایی آپلود کرده
            media_data = self.user_media.get(user_id, {'ids': [], 'type': 'product'})
            media_ids = media_data['ids']
            media_type = media_data['type']
            
            # اگه عکس‌ها آپلود شده، اطلاعات رو به prompt اضافه کن
            if media_ids:
                if media_type == 'product':
                    pinned_id = media_ids[0]  # اولین عکس = عکس اصلی
                    user_message += f"\n\nنکته مهم: {len(media_ids)} عکس آپلود شده با IDs: {media_ids}. "
                    user_message += f"عکس اصلی (pinned): {pinned_id}. "
                    user_message += f"لطفاً محصول رو با media_pinned_id={pinned_id} اضافه کن."
                elif media_type == 'category':
                    category_media_id = media_ids[0]  # فقط یک عکس برای دسته‌بندی
                    user_message += f"\n\nنکته: یک عکس برای دسته‌بندی آپلود شده (media_id: {category_media_id})."
            
            # پردازش درخواست با AI
            action_data = await self.ai_handler.process_request(user_message)
            
            # اگه محصول اضافه شد و media داره
            if action_data.get('action') == 'add_product' and media_ids and media_type == 'product':
                action_data['data']['media_pinned_id'] = media_ids[0]
                action_data['media_ids'] = media_ids  # برای لینک کردن بعد از ساخت
            
            # اگه دسته‌بندی اضافه شد و media داره
            elif action_data.get('action') == 'add_category' and media_ids and media_type == 'category':
                action_data['category_media_id'] = media_ids[0]
            
            # اجرای عملیات
            result = self.ai_handler.execute_action(action_data)
            
            # اگه محصول با موفقیت اضافه شد و media_ids داریم
            if result.get('success') and action_data.get('action') == 'add_product' and media_ids and media_type == 'product':
                product_id = result.get('product_id')
                if product_id:
                    # لینک کردن تمام عکس‌ها به محصول
                    linked = await self.image_handler.link_medias_to_product(media_ids, product_id)
                    if linked:
                        result['message'] += f"\n📸 {len(media_ids)} عکس به محصول لینک شد"
            
            # اگه دسته‌بندی با موفقیت اضافه شد و media داره
            elif result.get('success') and action_data.get('action') == 'add_category' and media_ids and media_type == 'category':
                category_id = result.get('category_id')
                if category_id:
                    # لینک کردن عکس به دسته‌بندی
                    linked = await self.image_handler.link_media_to_category(media_ids[0], category_id)
                    if linked:
                        result['message'] += f"\n📸 عکس به دسته‌بندی لینک شد"
            
            # حذف پیام "در حال پردازش"
            await processing_msg.delete()
            
            # ارسال پاسخ
            await update.message.reply_text(result['message'])
            
            # اگه محصول یا دسته‌بندی با موفقیت اضافه شد، media_ids رو پاک کن
            if result.get('success') and action_data.get('action') in ['add_product', 'add_category']:
                if user_id in self.user_media:
                    del self.user_media[user_id]
            
            if result.get('success'):
                logger.info(f"عملیات موفق: {action_data.get('action')}")
            else:
                logger.warning(f"عملیات ناموفق: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"خطا در پردازش پیام: {e}")
            await processing_msg.delete()
            await update.message.reply_text(
                config.MESSAGES['ai_error'].format(error=str(e))
            )

    def _is_authorized(self, user_id: int) -> bool:
        """بررسی دسترسی کاربر"""
        if not config.ADMIN_USER_IDS:
            return True  # اگر لیست ادمین خالی باشد، همه دسترسی دارند
        return user_id in config.ADMIN_USER_IDS

    def run(self):
        """اجرای بات"""
        logger.info("ربات در حال اجرا است...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """تابع اصلی"""
    try:
        bot = ShopBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("ربات متوقف شد.")
    except Exception as e:
        logger.error(f"خطای کلی: {e}")


if __name__ == '__main__':
    main()
