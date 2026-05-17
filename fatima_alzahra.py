import os
import asyncio
import re
import logging
import random
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, AuthKeyDuplicated
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ---------- إعدادات اللوجر ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_sniper.log'), logging.StreamHandler()]
)
logger = logging.getLogger("OmegaSniper")

# ---------- جلب الإعدادات من GitHub Secrets ----------
API_ID_1 = int(os.environ["API_ID_1"])
API_HASH_1 = os.environ["API_HASH_1"]
SESSION_1 = os.environ["SESSION_1"]

API_ID_2 = int(os.environ.get("API_ID_2") or os.environ.get("API_ID_1"))
API_HASH_2 = os.environ.get("API_HASH_2") or os.environ.get("API_HASH_1")
SESSION_2 = os.environ.get("SESSION_2", "")

ADMIN_ID = int(os.environ["ADMIN_ID"])

# ---------- تحديث الميزانية والنطاق الجديد ----------
GIFT_PRICE_MIN = 200
GIFT_PRICE_MAX = 250

# توسيع كلمات الروليت والمسابقات بشكل ضخم جداً
HUNT_KEYWORDS = [
    "مشاركة", "انضمام", "سحب", "دخول", "روليت", "هدية", "نجوم", "اضغط", "بسرعة", 
    "شارك", "انقر", "اضغط للانضمام", "انضم الآن", "سجل هنا", "التحق", "تأكيد", 
    "تفاعل", "انقر هنا", "دخول السحب", "سجل اسمك", "join", "click", "participate"
]
DANGER_WORDS = ["أكثر نجوم", "من يضع", "تصويت بنجوم", "اكثر شخص يحط", "مزاد"]

# معرفات أسواق الهدايا (ضع معرفات القنوات التي تراقبها هنا بدون @)
GIFT_MARKETS = ["Koda_7", "tonnel_network_bot", "AutoGiftsBot", "GiftHub_bot"]

PERSONA_NAMES = ["فاطمة الزهراء", "لارا", "ملاك", "سما"]
PERSONA_BIOS = ["مغربية 🇲🇦 | 18 سنة", "بنت بسيطة من المغرب"]

# معرفات الرسائل للوحة التحكم والبث الحي
PANEL_MSG_ID = None
LIVE_LOG_MSG_ID = None

class OmegaMultiSystem:
    def __init__(self):
        self.app1 = Client("account1", api_id=API_ID_1, api_hash=API_HASH_1, session_string=SESSION_1)
        self.app2 = Client("account2", api_id=API_ID_2, api_hash=API_HASH_2, session_string=SESSION_2) if SESSION_2 else None
        
        self.running = True
        self.sniper_enabled = True
        self.is_resting = False
        self.stats = {"wins": 0, "gifts_bought": 0, "msgs_processed": 0, "start_time": time.time()}
        self.last_scans = [] # للاحتفاظ بآخر عمليات فحص حية

    async def update_live_panel(self):
        """تحديث لوحة الإحصائيات وبث نتائج الفحص الحي في رسائل المدير"""
        global PANEL_MSG_ID, LIVE_LOG_MSG_ID
        if not self.running:
            return
            
        uptime = str(timedelta(seconds=int(time.time() - self.stats['start_time'])))
        status = "😴 راحة مؤقتة" if self.is_resting else "🟢 نشط ويصطاد"
        
        # 1. صياغة لوحة التحكم
        panel_text = (
            f"🔥 **لوحة تحكم Omega Sniper الحية**\n"
            f"-----------------------------------\n"
            f"Status: {status}\n"
            f"⏱️ مدة العمل المستمر: {uptime}\n"
            f"🏆 فوز روليت ومسابقات: {self.stats['wins']}\n"
            f"💎 هدايا تم صيدها بنجاح: {self.stats['gifts_bought']}\n"
            f"📨 رسائل تم تحليلها: {self.stats['msgs_processed']}\n"
            f"🎯 نطاق قنص الأسعار المستهدف: {GIFT_PRICE_MIN} - {GIFT_PRICE_MAX} ⭐\n"
            f"⚙️ حالة القناص الحالي: {'🟢 يعمل بسرعة البرق' if self.sniper_enabled else '🔴 معطل مؤقتاً'}"
        )
        
        # أزرار التحكم اللحظية
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎯 تفعيل القناص", callback_data="toggle_sniper_on"),
                InlineKeyboardButton("🔴 إيقاف القناص", callback_data="toggle_sniper_off")
            ],
            [
                InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data="refresh_stats")
            ]
        ])

        # 2. صياغة بث الفحص الحي (Live Log)
        log_text = "🔍 **نتائج الفحص الحي للقناص (Live Scan):**\n-----------------------------------\n"
        if not self.last_scans:
            log_text += "⏳ بانتظار تدفق الرسائل من الأسواق..."
        else:
            for scan in self.last_scans[-5:]: # إظهار آخر 5 عمليات فحص فقط لمنع التضخم
                log_text += f"{scan}\n"

        try:
            # تحديث أو إرسال لوحة التحكم
            if PANEL_MSG_ID:
                await self.app1.edit_message_text(ADMIN_ID, PANEL_MSG_ID, panel_text, reply_markup=keyboard)
            else:
                sent_panel = await self.app1.send_message(ADMIN_ID, panel_text, reply_markup=keyboard)
                PANEL_MSG_ID = sent_panel.id

            # تحديث أو إرسال البث الحي لنتائج الفحص
            if LIVE_LOG_MSG_ID:
                await self.app1.edit_message_text(ADMIN_ID, LIVE_LOG_MSG_ID, log_text)
            else:
                sent_log = await self.app1.send_message(ADMIN_ID, log_text)
                LIVE_LOG_MSG_ID = sent_log.id
        except Exception as e:
            logger.debug(f"خطأ في تحديث اللوحات: {e}")

    async def log_scan_result(self, channel_name, price, status_text):
        """إضافة نتيجة الفحص الحي وتحديث اللوحة فوراً"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"⏱️ [{timestamp}] | 📍 {channel_name} | 💰 {price}⭐ -> {status_text}"
        self.last_scans.append(log_entry)
        if len(self.last_scans) > 10:
            self.last_scans.pop(0)
        await self.update_live_panel()

    async def rest_controller(self):
        """تجنب الحظر التلقائي بالراحة الذكية"""
        while self.running:
            await asyncio.sleep(4 * 3600)
            self.is_resting = True
            await self.update_live_panel()
            await asyncio.sleep(15 * 60) # راحة 15 دقيقة
            self.is_resting = False
            await self.update_live_panel()

    async def process_message(self, client, message, account_tag):
        if not self.running or self.is_resting:
            return
        
        self.stats['msgs_processed'] += 1
        text = message.text or message.caption or ""
        chat = message.chat
        chat_title = chat.username or chat.title or "سوق"

        # 1. الحماية من فخاخ المسابقات
        if any(word in text for word in DANGER_WORDS):
            return

        # 2. القناص فائق السرعة - صيد الهدايا المطورة بالتفاعل مع الأزرار
        if self.sniper_enabled:
            # التحقق إذا كانت الرسالة من قنوات الماركت أو تحتوي على روابط الهدايا
            if chat.username in GIFT_MARKETS or any(link in text for link in ["t.me/nft/", "tg://nft", "t.me/gift/"]):
                detected_price = None
                target_button_index = None

                # البحث عن السعر في النص
                price_match = re.search(r'(\d+)\s*(🌟|نجمة|star|stars|⭐)', text, re.I)
                if price_match:
                    detected_price = int(price_match.group(1))

                # البحث عن السعر داخل الأزرار وزر الشراء المباشر
                if message.reply_markup:
                    for row_idx, row in enumerate(message.reply_markup.inline_keyboard):
                        for btn_idx, button in enumerate(row):
                            if any(k in button.text.lower() for k in ['شراء', 'اشتري', 'buy', 'purchase', 'get', '💎']):
                                target_button_index = button.index if hasattr(button, 'index') else btn_idx
                                if not detected_price:
                                    btn_price = re.search(r'(\d+)', button.text)
                                    if btn_price:
                                        detected_price = int(btn_price.group(1))

                # إذا اكتشف السعر يتم معالجته فوراً وبث النتيجة حية
                if detected_price:
                    if GIFT_PRICE_MIN <= detected_price <= GIFT_PRICE_MAX:
                        if target_button_index is not None:
                            # سرعة البرق: كبس الزر بملي ثواني عشوائية صغيرة جداً للتفوق على المنافسين
                            await asyncio.sleep(random.uniform(0.01, 0.08))
                            try:
                                await message.click(target_button_index)
                                self.stats['gifts_bought'] += 1
                                await self.log_scan_result(chat_title, detected_price, "🚀 [صيد ناجح بسعرك المطلوب!]")
                                # إرسال إشعار فوري منفصل للتأكيد
                                await client.send_message(ADMIN_ID, f"🎉 **[Omega - {account_tag}] صيد صاعق ناجح!**\n💰 السعر: {detected_price}⭐\n📍 المصدر: {chat_title}")
                                return
                            except FloodWait as e:
                                await asyncio.sleep(e.value + 1)
                            except Exception as e:
                                await self.log_scan_result(chat_title, detected_price, f"❌ فشل الضغط: {str(e)[:15]}")
                    else:
                        # بث مباشر لعملية الفحص الجارية لتراها في حسابك (خارج النطاق)
                        await self.log_scan_result(chat_title, detected_price, "❌ خارج ميزانيتك المقدرة")
                        return

        # 3. الروليت المطور - تفاعل فوري مع الكلمات المفتاحية الجديدة للأزرار التفاعلية
        if message.reply_markup:
            for row in message.reply_markup.inline_keyboard:
                for button in row:
                    if any(keyword in button.text.lower() for keyword in HUNT_KEYWORDS):
                        await asyncio.sleep(random.uniform(0.4, 1.2)) # سرعة منسقة لمنع التداخل للحسابين
                        try:
                            await message.click(button.index if hasattr(button, 'index') else 0)
                            self.stats['wins'] += 1
                            await self.update_live_panel()
                            return
                        except FloodWait as e:
                            await asyncio.sleep(e.value + 1)
                        except:
                            pass

    async def start_system(self):
        logger.info("🔄 جاري إقلاع قناص أوميجا المزدوج...")
        await self.app1.start()
        if self.app2:
            await self.app2.start()

        # تشغيل مستمعي الرسائل بالتوازي للحسابين ليعملا بنفس التناغم تماماً
        @self.app1.on_message(filters.all)
        async def h1(client, message):
            await self.process_message(client, message, "الحساب الأول")

        if self.app2:
            @self.app2.on_message(filters.all)
            async def h2(client, message):
                await self.process_message(client, message, "الحساب الثاني")

        # معالج أزرار لوحة التحكم التفاعلية القادمة من حسابك لإيقاف أو تشغيل القناص يدوياً
        @self.app1.on_callback_query()
        async def cb_handler(client, callback_query: CallbackQuery):
            if callback_query.from_user.id != ADMIN_ID:
                return
            data = callback_query.data
            if data == "toggle_sniper_on":
                self.sniper_enabled = True
                await callback_query.answer("🎯 تم تفعيل القناص بنجاح!")
            elif data == "toggle_sniper_off":
                self.sniper_enabled = False
                await callback_query.answer("🔴 تم إيقاف القناص مؤقتاً.")
            elif data == "refresh_stats":
                await callback_query.answer("🔄 تم تحديث الأرقام الحية.")
            await self.update_live_panel()

        # تشغيل المهام الدورية الخلفية حماية للاتصال المستمر
        asyncio.create_task(self.rest_controller())
        
        # إرسال اللوحة لأول مرة عند التشغيل بنجاح
        await self.update_live_panel()
        logger.info("🚀 الأنظمة نشطة بالكامل وبث الفحص الحي بدأ.")
        await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(OmegaMultiSystem().start_system())

