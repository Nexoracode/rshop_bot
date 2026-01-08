import os
import time
from ftplib import FTP
from typing import Optional, Dict, List
import config
from database import Database


class ImageHandler:
    """مدیریت آپلود تصاویر به FTP و ذخیره در دیتابیس"""
    
    def __init__(self):
        self.db = Database()
        self.ftp_config = config.FTP_CONFIG
    
    async def upload_image(self, image_path: str, product_id: Optional[int] = None, 
                          category_id: Optional[int] = None) -> Dict:
        """
        آپلود تصویر به FTP و ذخیره در دیتابیس
        
        Args:
            image_path: مسیر فایل تصویر
            product_id: شناسه محصول (اختیاری)
            category_id: شناسه دسته‌بندی (اختیاری)
            
        Returns:
            dict با media_id و url
        """
        try:
            # ساخت نام فایل یونیک
            timestamp = int(time.time() * 1000)
            file_extension = os.path.splitext(image_path)[1]
            filename = f"file-{timestamp}{file_extension}"
            
            # آپلود به FTP
            ftp_url = self._upload_to_ftp(image_path, filename)
            
            if not ftp_url:
                raise Exception("خطا در آپلود به FTP")
            
            # ذخیره در دیتابیس
            media_data = {
                'url': ftp_url,
                'type': 'image',
                'product_id': product_id,
                'category_id': category_id
            }
            
            media_id = self.db.add_media(media_data)
            
            return {
                'success': True,
                'media_id': media_id,
                'url': ftp_url,
                'filename': filename
            }
            
        except Exception as e:
            print(f"خطا در آپلود تصویر: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def link_media_to_category(self, media_id: int, category_id: int) -> bool:
        """
        لینک کردن media به دسته‌بندی
        
        Args:
            media_id: شناسه media
            category_id: شناسه دسته‌بندی
            
        Returns:
            bool موفقیت عملیات
        """
        try:
            query = "UPDATE medias SET category_id = %s WHERE id = %s"
            self.db.execute_query(query, (category_id, media_id))
            
            print(f"✅ عکس به دسته‌بندی {category_id} لینک شد")
            return True
            
        except Exception as e:
            print(f"❌ خطا در لینک media به دسته‌بندی: {e}")
            return False
    
    async def link_medias_to_product(self, media_ids: List[int], product_id: int) -> bool:
        """
        لینک کردن چندین media به یک محصول
        
        Args:
            media_ids: لیست media_id ها
            product_id: شناسه محصول
            
        Returns:
            bool موفقیت عملیات
        """
        try:
            for media_id in media_ids:
                query = "UPDATE medias SET product_id = %s WHERE id = %s"
                self.db.execute_query(query, (product_id, media_id))
            
            print(f"✅ {len(media_ids)} عکس به محصول {product_id} لینک شد")
            return True
            
        except Exception as e:
            print(f"❌ خطا در لینک media ها: {e}")
            return False
    
    def _upload_to_ftp(self, local_file: str, remote_filename: str) -> Optional[str]:
        """آپلود فایل به FTP"""
        try:
            # اتصال به FTP
            ftp = FTP()
            ftp.connect(
                self.ftp_config['host'], 
                self.ftp_config['port']
            )
            ftp.login(
                self.ftp_config['user'], 
                self.ftp_config['password']
            )
            
            # تغییر به پوشه مقصد
            try:
                ftp.cwd(self.ftp_config['base_path'])
            except:
                # اگر پوشه وجود نداره، بسازش
                self._create_ftp_directory(ftp, self.ftp_config['base_path'])
                ftp.cwd(self.ftp_config['base_path'])
            
            # آپلود فایل
            with open(local_file, 'rb') as file:
                ftp.storbinary(f'STOR {remote_filename}', file)
            
            ftp.quit()
            
            # ساخت URL کامل
            full_url = self.ftp_config['base_url'] + remote_filename
            print(f"✅ فایل آپلود شد: {full_url}")
            
            return full_url
            
        except Exception as e:
            print(f"❌ خطا در FTP: {e}")
            return None
    
    def _create_ftp_directory(self, ftp: FTP, path: str):
        """ساخت دایرکتوری در FTP"""
        dirs = path.strip('/').split('/')
        for directory in dirs:
            try:
                ftp.cwd(directory)
            except:
                ftp.mkd(directory)
                ftp.cwd(directory)
    
    def get_media_by_id(self, media_id: int) -> Optional[Dict]:
        """دریافت اطلاعات رسانه با ID"""
        query = "SELECT * FROM medias WHERE id = %s"
        result = self.db.execute_query(query, (media_id,), fetch=True)
        return result[0] if result else None
    
    def get_product_medias(self, product_id: int) -> List[Dict]:
        """دریافت تمام media های یک محصول"""
        return self.db.get_product_medias(product_id)
    
    def delete_image(self, media_id: int) -> bool:
        """حذف تصویر از دیتابیس"""
        try:
            query = "DELETE FROM medias WHERE id = %s"
            self.db.execute_query(query, (media_id,))
            return True
        except Exception as e:
            print(f"خطا در حذف media: {e}")
            return False
