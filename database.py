import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any
import config
from datetime import datetime


class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """اتصال به دیتابیس MySQL"""
        try:
            self.connection = mysql.connector.connect(**config.DB_CONFIG)
            if self.connection.is_connected():
                print("اتصال به دیتابیس MySQL برقرار شد.")
        except Error as e:
            print(f"خطا در اتصال به دیتابیس: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """اجرای کوئری"""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"خطا در اجرای کوئری: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    # ==================== محصولات ====================
    
    def add_product(self, product_data: Dict[str, Any]) -> int:
        """افزودن محصول جدید"""
        query = """
        INSERT INTO products (
            name, price, stock, sku, category_id, brand_id,
            description, weight, weight_unit, is_same_day_shipping,
            requires_preparation, preparation_days, is_limited_stock,
            discount_amount, discount_percent, is_featured,
            is_visible, is_active, order_limit
        ) VALUES (
            %(name)s, %(price)s, %(stock)s, %(sku)s, %(category_id)s, %(brand_id)s,
            %(description)s, %(weight)s, %(weight_unit)s, %(is_same_day_shipping)s,
            %(requires_preparation)s, %(preparation_days)s, %(is_limited_stock)s,
            %(discount_amount)s, %(discount_percent)s, %(is_featured)s,
            %(is_visible)s, %(is_active)s, %(order_limit)s
        )
        """
        
        # مقادیر پیش‌فرض
        defaults = {
            'stock': 0,
            'weight': 0,
            'weight_unit': 'کیلوگرم',
            'is_same_day_shipping': 0,
            'requires_preparation': 0,
            'preparation_days': None,
            'is_limited_stock': 0,
            'discount_amount': 0,
            'discount_percent': 0,
            'is_featured': 0,
            'is_visible': 1,
            'is_active': 1,
            'order_limit': None,
            'description': None,
            'brand_id': None
        }
        
        # ترکیب مقادیر پیش‌فرض با داده‌های ورودی
        product_data = {**defaults, **product_data}
        
        return self.execute_query(query, product_data)

    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> bool:
        """ویرایش محصول"""
        # ساخت dynamic query برای فیلدهایی که باید به‌روزرسانی شوند
        set_clause = ", ".join([f"{key} = %({key})s" for key in product_data.keys()])
        query = f"UPDATE products SET {set_clause} WHERE id = %(id)s"
        
        product_data['id'] = product_id
        self.execute_query(query, product_data)
        return True

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """دریافت محصول با ID"""
        query = """
        SELECT p.*, c.title as category_name, b.name as brand_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE p.id = %s
        """
        result = self.execute_query(query, (product_id,), fetch=True)
        return result[0] if result else None

    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """جستجوی محصول با نام"""
        query = """
        SELECT p.*, c.title as category_name, b.name as brand_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE p.name LIKE %s
        """
        result = self.execute_query(query, (f'%{name}%',), fetch=True)
        return result[0] if result else None

    def get_all_products(self, limit: int = 50) -> List[Dict]:
        """دریافت لیست محصولات"""
        query = """
        SELECT p.id, p.name, p.price, p.stock, c.title as category_name, 
               b.name as brand_name, p.is_active
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN brands b ON p.brand_id = b.id
        ORDER BY p.created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (limit,), fetch=True)

    def delete_product(self, product_id: int) -> bool:
        """حذف محصول"""
        query = "DELETE FROM products WHERE id = %s"
        self.execute_query(query, (product_id,))
        return True

    # ==================== دسته‌بندی‌ها ====================
    
    def add_category(self, category_data: Dict[str, Any]) -> int:
        """افزودن دسته‌بندی جدید"""
        query = """
        INSERT INTO categories (
            title, slug, description, parent_id, level, 
            discount, display_order, is_active
        ) VALUES (
            %(title)s, %(slug)s, %(description)s, %(parent_id)s, %(level)s,
            %(discount)s, %(display_order)s, %(is_active)s
        )
        """
        
        defaults = {
            'description': None,
            'parent_id': None,
            'level': 0,
            'discount': None,
            'display_order': 0,
            'is_active': 1
        }
        
        category_data = {**defaults, **category_data}
        return self.execute_query(query, category_data)

    def get_category_by_name(self, title: str) -> Optional[Dict]:
        """جستجوی دسته‌بندی با نام"""
        query = "SELECT * FROM categories WHERE title LIKE %s"
        result = self.execute_query(query, (f'%{title}%',), fetch=True)
        return result[0] if result else None

    def get_category_by_id(self, category_id: int) -> Optional[Dict]:
        """دریافت دسته‌بندی با ID"""
        query = "SELECT * FROM categories WHERE id = %s"
        result = self.execute_query(query, (category_id,), fetch=True)
        return result[0] if result else None

    def get_all_categories(self) -> List[Dict]:
        """دریافت لیست تمام دسته‌بندی‌ها"""
        query = """
        SELECT c.*, p.title as parent_name
        FROM categories c
        LEFT JOIN categories p ON c.parent_id = p.id
        ORDER BY c.level, c.display_order
        """
        return self.execute_query(query, fetch=True)

    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> bool:
        """ویرایش دسته‌بندی"""
        set_clause = ", ".join([f"{key} = %({key})s" for key in category_data.keys()])
        query = f"UPDATE categories SET {set_clause} WHERE id = %(id)s"
        
        category_data['id'] = category_id
        self.execute_query(query, category_data)
        return True

    def delete_category(self, category_id: int) -> bool:
        """حذف دسته‌بندی"""
        query = "DELETE FROM categories WHERE id = %s"
        self.execute_query(query, (category_id,))
        return True

    # ==================== برندها ====================
    
    def add_brand(self, brand_data: Dict[str, Any]) -> int:
        """افزودن برند جدید"""
        query = """
        INSERT INTO brands (name, slug, logo, is_active)
        VALUES (%(name)s, %(slug)s, %(logo)s, %(is_active)s)
        """
        
        defaults = {
            'logo': '',
            'is_active': 1
        }
        
        brand_data = {**defaults, **brand_data}
        return self.execute_query(query, brand_data)

    def get_brand_by_name(self, name: str) -> Optional[Dict]:
        """جستجوی برند با نام"""
        query = "SELECT * FROM brands WHERE name LIKE %s"
        result = self.execute_query(query, (f'%{name}%',), fetch=True)
        return result[0] if result else None

    def get_all_brands(self) -> List[Dict]:
        """دریافت لیست تمام برندها"""
        query = "SELECT * FROM brands ORDER BY name"
        return self.execute_query(query, fetch=True)

    def update_brand(self, brand_id: int, brand_data: Dict[str, Any]) -> bool:
        """ویرایش برند"""
        set_clause = ", ".join([f"{key} = %({key})s" for key in brand_data.keys()])
        query = f"UPDATE brands SET {set_clause} WHERE id = %(id)s"
        
        brand_data['id'] = brand_id
        self.execute_query(query, brand_data)
        return True

    def delete_brand(self, brand_id: int) -> bool:
        """حذف برند"""
        query = "DELETE FROM brands WHERE id = %s"
        self.execute_query(query, (brand_id,))
        return True

    # ==================== ویژگی‌ها ====================
    
    def add_attribute(self, attribute_data: Dict[str, Any]) -> int:
        """افزودن ویژگی جدید"""
        query = """
        INSERT INTO attributes (
            name, slug, type, is_public, is_variant, 
            group_id, display_order, is_active
        ) VALUES (
            %(name)s, %(slug)s, %(type)s, %(is_public)s, %(is_variant)s,
            %(group_id)s, %(display_order)s, %(is_active)s
        )
        """
        
        defaults = {
            'type': 'text',
            'is_public': 0,
            'is_variant': 0,
            'group_id': None,
            'display_order': 0,
            'is_active': 1
        }
        
        attribute_data = {**defaults, **attribute_data}
        return self.execute_query(query, attribute_data)

    def get_all_attributes(self) -> List[Dict]:
        """دریافت لیست تمام ویژگی‌ها"""
        query = """
        SELECT a.*, ag.name as group_name
        FROM attributes a
        LEFT JOIN attribute_groups ag ON a.group_id = ag.id
        ORDER BY a.display_order
        """
        return self.execute_query(query, fetch=True)

    # ==================== راهنمای محصول ====================
    
    def add_helper(self, helper_data: Dict[str, Any]) -> int:
        """افزودن راهنمای محصول"""
        query = """
        INSERT INTO helpers (title, description, image, product_id)
        VALUES (%(title)s, %(description)s, %(image)s, %(product_id)s)
        """
        
        defaults = {
            'image': None
        }
        
        helper_data = {**defaults, **helper_data}
        return self.execute_query(query, helper_data)

    def get_helper_by_product(self, product_id: int) -> Optional[Dict]:
        """دریافت راهنمای محصول"""
        query = "SELECT * FROM helpers WHERE product_id = %s"
        result = self.execute_query(query, (product_id,), fetch=True)
        return result[0] if result else None

    # ==================== رسانه‌ها ====================
    
    def add_media(self, media_data: Dict[str, Any]) -> int:
        """افزودن رسانه (تصویر/ویدیو)"""
        query = """
        INSERT INTO medias (url, type, alt_text, product_id, category_id, user_id)
        VALUES (%(url)s, %(type)s, %(alt_text)s, %(product_id)s, %(category_id)s, %(user_id)s)
        """
        
        defaults = {
            'type': 'image',
            'alt_text': None,
            'product_id': None,
            'category_id': None,
            'user_id': None
        }
        
        media_data = {**defaults, **media_data}
        return self.execute_query(query, media_data)

    def get_product_medias(self, product_id: int) -> List[Dict]:
        """دریافت رسانه‌های محصول"""
        query = "SELECT * FROM medias WHERE product_id = %s ORDER BY created_at"
        return self.execute_query(query, (product_id,), fetch=True)

    # ==================== جستجو ====================
    
    def search_products(self, search_term: str, limit: int = 20) -> List[Dict]:
        """جستجوی محصولات"""
        query = """
        SELECT p.id, p.name, p.price, p.stock, c.title as category_name, 
               b.name as brand_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE p.name LIKE %s OR p.description LIKE %s OR p.sku LIKE %s
        ORDER BY p.created_at DESC
        LIMIT %s
        """
        search_pattern = f'%{search_term}%'
        return self.execute_query(query, (search_pattern, search_pattern, search_pattern, limit), fetch=True)

    def close(self):
        """بستن اتصال دیتابیس"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("اتصال دیتابیس بسته شد.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
