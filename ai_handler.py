import json
from typing import Dict, Any, Optional
import config
from database import Database

# Import کتابخانه‌های AI
if config.AI_PROVIDER == 'groq':
    from groq import Groq
elif config.AI_PROVIDER == 'claude':
    import anthropic


class AIHandler:
    def __init__(self):
        self.provider = config.AI_PROVIDER
        self.db = Database()
        
        # Initialize AI client بر اساس provider
        if self.provider == 'groq':
            self.client = Groq(api_key=config.GROQ_API_KEY)
            self.model = config.GROQ_MODEL
            print(f"✅ استفاده از Groq (رایگان) - مدل: {self.model}")
        elif self.provider == 'claude':
            self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self.model = config.CLAUDE_MODEL
            print(f"✅ استفاده از Claude (پولی) - مدل: {self.model}")
        else:
            raise ValueError(f"AI Provider نامعتبر: {self.provider}")

    def create_system_prompt(self) -> str:
        """ساخت system prompt"""
        
        # دریافت اطلاعات دسته‌بندی‌ها و برندها
        categories = self.db.get_all_categories()
        brands = self.db.get_all_brands()
        
        categories_text = "\n".join([f"- {cat['title']} (ID: {cat['id']})" for cat in categories])
        brands_text = "\n".join([f"- {brand['name']} (ID: {brand['id']})" for brand in brands])
        
        return f"""شما یک دستیار هوشمند برای مدیریت فروشگاه آنلاین هستید.

وظایف شما:
1. درک درخواست‌های کاربر به زبان فارسی ساده
2. استخراج اطلاعات محصول، دسته‌بندی، برند و ویژگی‌ها
3. تولید پاسخ JSON استاندارد برای اجرای دستورات

دسته‌بندی‌های موجود:
{categories_text if categories else "هیچ دسته‌بندی موجود نیست"}

برندهای موجود:
{brands_text if brands else "هیچ برندی موجود نیست"}

ساختار جدول محصولات (products):
- name: نام محصول (اجباری)
- price: قیمت (اجباری، عدد)
- stock: موجودی انبار (عدد)
- sku: کد محصول (اجباری، یونیک)
- category_id: شناسه دسته‌بندی (اجباری)
- brand_id: شناسه برند
- description: توضیحات
- weight: وزن محصول
- weight_unit: واحد وزن (کیلوگرم یا گرم)

انواع عملیات‌ها و فرمت JSON خروجی:

1. افزودن محصول:
{{
    "action": "add_product",
    "data": {{
        "name": "نام محصول",
        "price": 1000000,
        "sku": "SKU-001",
        "category_id": 1,
        "brand_id": 1,
        "stock": 10
    }},
    "message": "پیام تأیید"
}}

2. ویرایش محصول:
{{
    "action": "update_product",
    "product_identifier": "نام یا ID",
    "data": {{"price": 1200000}},
    "message": "پیام تأیید"
}}

3. حذف محصول:
{{
    "action": "delete_product",
    "product_identifier": "نام یا ID",
    "message": "پیام تأیید"
}}

4. لیست محصولات:
{{
    "action": "list_products",
    "message": "لیست محصولات"
}}

5. جستجو:
{{
    "action": "search_product",
    "search_term": "کلمه کلیدی",
    "message": "جستجو"
}}

6. افزودن دسته‌بندی:
{{
    "action": "add_category",
    "data": {{"title": "نام", "slug": "slug"}},
    "message": "پیام"
}}

7. افزودن برند:
{{
    "action": "add_brand",
    "data": {{"name": "نام", "slug": "slug"}},
    "message": "پیام"
}}

8. لیست دسته‌بندی‌ها:
{{
    "action": "list_categories",
    "message": "لیست"
}}

9. لیست برندها:
{{
    "action": "list_brands",
    "message": "لیست"
}}

10. جزئیات محصول:
{{
    "action": "view_product",
    "product_identifier": "نام یا ID",
    "message": "جزئیات"
}}

نکات مهم:
- SKU را خودکار تولید کن از نام محصول
- قیمت فقط عدد (بدون تومان)
- slug از نام با حروف انگلیسی و خط تیره
- در پیام‌ها از ایموجی استفاده کن
- فقط JSON برگردان بدون هیچ توضیح اضافی
"""

    async def process_request(self, user_message: str) -> Dict[str, Any]:
        """پردازش درخواست با AI provider انتخابی"""
        try:
            system_prompt = self.create_system_prompt()
            
            if self.provider == 'groq':
                return await self._process_with_groq(system_prompt, user_message)
            elif self.provider == 'claude':
                return await self._process_with_claude(system_prompt, user_message)
                
        except Exception as e:
            print(f"خطا در پردازش درخواست: {e}")
            return {
                "action": "error",
                "message": f"خطایی رخ داد: {str(e)}"
            }

    async def _process_with_groq(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """پردازش با Groq (رایگان)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            return self._parse_json_response(response_text)
            
        except Exception as e:
            raise Exception(f"خطای Groq: {str(e)}")

    async def _process_with_claude(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """پردازش با Claude (پولی)"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            
            response_text = message.content[0].text
            return self._parse_json_response(response_text)
            
        except Exception as e:
            raise Exception(f"خطای Claude: {str(e)}")

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """پارس کردن پاسخ JSON"""
        try:
            # پاکسازی
            response_text = response_text.strip()
            
            # حذف markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # استخراج JSON
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                response_text = response_text[start:end]
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            print(f"خطا در پارس JSON: {e}")
            print(f"پاسخ: {response_text}")
            return {
                "action": "error",
                "message": "متأسفانه نتوانستم درخواست شما را درک کنم."
            }

    def execute_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """اجرای عملیات"""
        action = action_data.get('action')
        
        try:
            if action == 'add_product':
                return self._add_product(action_data)
            elif action == 'update_product':
                return self._update_product(action_data)
            elif action == 'delete_product':
                return self._delete_product(action_data)
            elif action == 'list_products':
                return self._list_products(action_data)
            elif action == 'search_product':
                return self._search_product(action_data)
            elif action == 'view_product':
                return self._view_product(action_data)
            elif action == 'add_category':
                return self._add_category(action_data)
            elif action == 'list_categories':
                return self._list_categories(action_data)
            elif action == 'add_brand':
                return self._add_brand(action_data)
            elif action == 'list_brands':
                return self._list_brands(action_data)
            else:
                return {
                    'success': False,
                    'message': action_data.get('message', 'عملیات ناشناخته')
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'خطا: {str(e)}'
            }

    def _add_product(self, action_data: Dict) -> Dict:
        product_data = action_data.get('data', {})
        if 'category_id' in product_data:
            category = self.db.get_category_by_id(product_data['category_id'])
            if not category:
                return {'success': False, 'message': '❌ دسته‌بندی یافت نشد'}
        
        product_id = self.db.add_product(product_data)
        return {
            'success': True,
            'message': f"✅ {action_data.get('message', 'محصول اضافه شد')}\n🆔 ID: {product_id}",
            'product_id': product_id
        }

    def _update_product(self, action_data: Dict) -> Dict:
        identifier = action_data.get('product_identifier')
        product_data = action_data.get('data', {})
        
        product = self.db.get_product_by_id(identifier) if isinstance(identifier, int) else self.db.get_product_by_name(identifier)
        if not product:
            return {'success': False, 'message': '❌ محصول یافت نشد'}
        
        self.db.update_product(product['id'], product_data)
        return {'success': True, 'message': f"✅ {action_data.get('message', 'محصول ویرایش شد')}"}

    def _delete_product(self, action_data: Dict) -> Dict:
        identifier = action_data.get('product_identifier')
        product = self.db.get_product_by_id(identifier) if isinstance(identifier, int) else self.db.get_product_by_name(identifier)
        if not product:
            return {'success': False, 'message': '❌ محصول یافت نشد'}
        
        self.db.delete_product(product['id'])
        return {'success': True, 'message': f"✅ محصول '{product['name']}' حذف شد"}

    def _list_products(self, action_data: Dict) -> Dict:
        products = self.db.get_all_products(limit=50)
        if not products:
            return {'success': True, 'message': '📋 محصولی یافت نشد'}
        
        message = "📋 لیست محصولات:\n\n"
        for idx, p in enumerate(products, 1):
            message += f"{idx}. {'✅' if p['is_active'] else '❌'} {p['name']}\n"
            message += f"   💰 {p['price']:,} تومان | 📦 {p['stock']}\n\n"
        return {'success': True, 'message': message}

    def _search_product(self, action_data: Dict) -> Dict:
        term = action_data.get('search_term', '')
        products = self.db.search_products(term)
        if not products:
            return {'success': True, 'message': f'🔍 نتیجه‌ای برای "{term}" یافت نشد'}
        
        message = f"🔍 نتایج '{term}':\n\n"
        for idx, p in enumerate(products, 1):
            message += f"{idx}. {p['name']}\n   💰 {p['price']:,} تومان\n\n"
        return {'success': True, 'message': message}

    def _view_product(self, action_data: Dict) -> Dict:
        identifier = action_data.get('product_identifier')
        product = self.db.get_product_by_id(identifier) if isinstance(identifier, int) else self.db.get_product_by_name(identifier)
        if not product:
            return {'success': False, 'message': '❌ محصول یافت نشد'}
        
        message = f"📦 {product['name']}\n"
        message += f"💰 {product['price']:,} تومان\n"
        message += f"📦 موجودی: {product['stock']}\n"
        message += f"🆔 {product['sku']}\n"
        return {'success': True, 'message': message}

    def _add_category(self, action_data: Dict) -> Dict:
        category_id = self.db.add_category(action_data.get('data', {}))
        return {'success': True, 'message': f"✅ دسته‌بندی اضافه شد\n🆔 ID: {category_id}", 'category_id': category_id}

    def _list_categories(self, action_data: Dict) -> Dict:
        categories = self.db.get_all_categories()
        if not categories:
            return {'success': True, 'message': '📋 دسته‌بندی یافت نشد'}
        
        message = "📂 دسته‌بندی‌ها:\n\n"
        for idx, c in enumerate(categories, 1):
            message += f"{idx}. {'✅' if c['is_active'] else '❌'} {c['title']}\n"
        return {'success': True, 'message': message}

    def _add_brand(self, action_data: Dict) -> Dict:
        brand_id = self.db.add_brand(action_data.get('data', {}))
        return {'success': True, 'message': f"✅ برند اضافه شد\n🆔 ID: {brand_id}"}

    def _list_brands(self, action_data: Dict) -> Dict:
        brands = self.db.get_all_brands()
        if not brands:
            return {'success': True, 'message': '📋 برندی یافت نشد'}
        
        message = "🔖 برندها:\n\n"
        for idx, b in enumerate(brands, 1):
            message += f"{idx}. {'✅' if b['is_active'] else '❌'} {b['name']}\n"
        return {'success': True, 'message': message}
