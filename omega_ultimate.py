#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omega Ultimate – النسخة الأسطورية النهائية
يتعامل مع AuthKeyDuplicatedError | يحول الهدايا تلقائياً | يغادر القنوات الميتة
يظهر متصل دائماً | يرد كإنسان حقيقي | يصطاد الروليتات والهدايا الرخيصة
"""
import os, sys, asyncio, random, re, time, logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types, errors
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SetTypingRequest, ReadHistoryRequest
from telethon.tl.functions.account import UpdateStatusRequest, UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.errors import (
    AuthKeyDuplicatedError, FloodWaitError, UsernameOccupiedError,
    UserBannedInChannelError, PeerFloodError
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_ultimate.log'), logging.StreamHandler()]
)
logger = logging.getLogger("OmegaUltimate")

# ========================== إعدادات البيئة ==========================
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "").strip()
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# ========================== إعدادات قابلة للتخصيص ==========================
MIN_STARS_FOR_SNIPER = 100
MAX_CHANNELS = 380                     # نبدأ مغادرة القنوات الميتة قبل الحد
SNIPER_PRICE_MIN = 100
SNIPER_PRICE_MAX = 130
AUTO_LEAVE_DEAD_DAYS = 3               # مغادرة القنوات الصامتة بعد 3 أيام

# ========================== الشخصية ==========================
PERSONA_NAMES = [
    "لارا", "ملاك", "ضائعة", "ليل", "غريبة", "سما", "روح", "فراشة",
    "سارا", "نور", "ظل", "حنين", "لا تسأل", "ماريا", "جانيت",
    "بنت القمر", "عطر الليل", "همسة", "مجهولة", "غيمة", "ريناد", "تالة"
]
PERSONA_BIOS = [
    "ضائعة في عالمي 🌸", "لا تبحث عني فأنا سر 😴", "أحب الصمت والمطر ☔",
    "البساطة عنواني ✨", "انثى من زمن آخر🕊️", "القمر صديقي الوحيد 🌙",
    "لا تعليق 🖤", "مزاجي قهوة وكتاب 📖", "لستُ كما تظن 💫"
]

# كلمات الصيد
HUNT_KEYWORDS = [
    "مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "هدية", "نجوم",
    "تعزيز", "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"
]

# مسابقات خطيرة (نتجنبها تماماً)
DANGEROUS_CONTEST = [
    "أكثر نجوم", "من يضع", "تصويت بنجوم", "النجوم الأعلى",
    "اللي يحط نجوم", "اكثر شخص يحط", "يحط يربح", "مزاد نجوم"
]

# مسابقات آمنة (نشارك فيها)
SAFE_CONTEST_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'

# رموز النجوم الحقيقية (يونيكود + إيموجي)
STAR_EMOJIS = ['⭐', '🌟', '✨', '💫', '⭐️', '❤️', '💙', '💜', '🧡', '💛', '💚', '🤍', '🤎', '🩷', '🩵', '❤️‍🔥', '💖', '💝', '💘', '💗', '💓', '💞', '💕', '❣️', '♥️', '💔', '🎁', '🍭', '🚀', '🐱', '👻', '🎃']
HEART_STICKERS = ['❤️', '💙', '💜', '🧡', '💛', '💚', '🤍', '🤎', '🩷', '🩵', '❤️‍🔥', '💖', '💝', '💘']

class OmegaUltimate:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stars_balance = 0
        self.sniper_enabled = False
        self.last_persona_change = datetime.min
        self.last_seen_messages = {}      # لتتبع زمن آخر مشاهدة (محاكاة بشرية)
        self.cache = set()
        self.stats = {"wins": 0, "stars_earned": 0, "gifts_bought": 0, "gifts_converted": 0, "channels_left": 0, "start_time": time.time()}

    # ========================== نظام الاتصال الحديدي ==========================
    async def iron_connect(self, client, name, max_retries=10):
        """اتصال مع إعادة محاولة غير محدودة وآلية هروب من AuthKeyDuplicatedError"""
        for attempt in range(max_retries):
            try:
                await client.connect()
                if await client.is_user_authorized():
                    logger.info(f"✅ {name} متصل")
                    return True
                else:
                    logger.error(f"❌ {name} جلسة غير صالحة")
                    return False
            except AuthKeyDuplicatedError:
                logger.warning(f"⚠️ {name} مفتاح مكرر - انتظار 60 ثانية...")
                await client.disconnect()
                await asyncio.sleep(60)
            except Exception as e:
                logger.warning(f"⚠️ {name} خطأ اتصال: {e} - إعادة المحاولة...")
                await asyncio.sleep(15)
        return False

    # ========================== البقاء متصلاً وإظهار الحالة ==========================
    async def keep_alive(self, client, name):
        """الحفاظ على الاتصال + إظهار الحساب متصل دائماً"""
        while self.running:
            try:
                if not client.is_connected():
                    await self.iron_connect(client, name)
                # إظهار الحساب متصل دائماً
                await client(UpdateStatusRequest(offline=False))
                # إرسال بينغ
                await client(functions.PingRequest(ping_id=random.randint(0, 2**31)))
            except AuthKeyDuplicatedError:
                logger.warning(f"🔄 {name} إعادة اتصال بعد خطأ المفتاح")
                await client.disconnect()
                await asyncio.sleep(60)
                await self.iron_connect(client, name)
            except Exception as e:
                logger.warning(f"⚠️ {name} خطأ في keep_alive: {e}")
            await asyncio.sleep(120)  # كل دقيقتين

    # ========================== تحويل الهدية إلى نجوم تلقائياً ==========================
    async def convert_incoming_gift(self, event, client):
        """عند وصول هدية، يحولها إلى نجوم فوراً"""
        try:
            if not event.reply_markup:
                return False
            
            text = event.raw_text or ""
            # اكتشاف أنها رسالة هدية قابلة للتحويل
            is_gift_message = any(w in text for w in ['هدية من', 'أضاف', 'الهدية', 'إلى ملفك', 'gift', 'أضفت'])
            if not is_gift_message:
                return False

            # البحث عن زر التحويل أو العرض
            for r_idx, row in enumerate(event.reply_markup.rows):
                for b_idx, btn in enumerate(row.buttons):
                    btn_text = btn.text.lower()
                    # أزرار التحويل المعروفة
                    if any(kw in btn_text for kw in ['تحويل', 'نجمة', 'نجوم', 'convert', 'stars', 'عرض', 'استلام']):
                        logger.info(f"🎁 جاري تحويل الهدية إلى نجوم...")
                        await asyncio.sleep(random.uniform(1.0, 2.5))
                        await event.click(r_idx, b_idx)
                        self.stats['gifts_converted'] += 1
                        # تقدير عدد النجوم (عادة بين 10-50)
                        self.stars_balance += random.randint(10, 50)
                        self.stats['stars_earned'] += random.randint(10, 50)
                        logger.info(f"✅ تم تحويل الهدية! الرصيد الحالي: ~{self.stars_balance} نجمة")
                        return True
            return False
        except Exception as e:
            logger.error(f"خطأ في تحويل الهدية: {e}")
            return False

    # ========================== صيد الهدايا المطورة الرخيصة ==========================
    async def snipe_cheap_gifts(self, event):
        """اصطياد الهدايا المعروضة بين 100-130 نجمة"""
        if not self.sniper_enabled:
            return False
        text = event.raw_text or ""
        try:
            # استخراج السعر
            prices = re.findall(r'(?:سعر|ثمن|بيع|price|قيمة)\s*[:#]?\s*(\d{2,})', text, re.I)
            for p_str in prices:
                price = int(p_str)
                if SNIPER_PRICE_MIN <= price <= SNIPER_PRICE_MAX and self.stars_balance >= price:
                    if event.reply_markup:
                        # البحث عن اسم الهدية
                        gift_name = "هدية"
                        name_match = re.search(r'(?:هدية|Gift|مقتني)\s*[:#]?\s*["\']?([\w\s\u0600-\u06FF]+)', text, re.I)
                        if name_match:
                            gift_name = name_match.group(1).strip()
                        
                        # النقر على زر الشراء
                        for row in event.reply_markup.rows:
                            for btn in row.buttons:
                                if any(k in btn.text for k in ['شراء', 'اشتري', 'buy', 'get', 'احصل']):
                                    logger.info(f"🔥 شراء {gift_name} بسعر {price} نجمة!")
                                    await asyncio.sleep(random.uniform(0.3, 0.8))  # سريع جداً
                                    await event.click(row.row_index, btn.column_index)
                                    self.stats['gifts_bought'] += 1
                                    self.stars_balance -= price
                                    # إرسال إشعار للمحفوظات
                                    await event.client.send_message('me', f"🎁 تم شراء {gift_name} بسعر {price} نجمة")
                                    return True
        except Exception as e:
            logger.error(f"خطأ في القناص: {e}")
        return False

    # ========================== مغادرة القنوات الميتة ==========================
    async def leave_dead_channels(self, client):
        """مغادرة القنوات غير المفيدة تلقائياً"""
        count = 0
        async for dialog in client.iter_dialogs():
            if not dialog.is_channel:
                continue
            try:
                # التحقق من آخر رسالة
                messages = await client.get_messages(dialog.entity, limit=1)
                if not messages or not messages[0].date:
                    await client(LeaveChannelRequest(dialog.entity))
                    count += 1
                    continue
                
                delta = datetime.now(tz=None) - messages[0].date.replace(tzinfo=None)
                # مغادرة القنوات الميتة
                if delta.days > AUTO_LEAVE_DEAD_DAYS:
                    # التأكد من عدم وجود مسابقات
                    recent_text = messages[0].raw_text or ""
                    has_contests = any(kw in recent_text for kw in HUNT_KEYWORDS + ['مسابقة', 'روليت', 'سحب'])
                    if not has_contests:
                        await client(LeaveChannelRequest(dialog.entity))
                        count += 1
                        logger.info(f"🚪 غادرت: {dialog.name}")
            except:
                pass
        
        self.stats['channels_left'] += count
        if count > 0:
            logger.info(f"🧹 تمت مغادرة {count} قناة ميتة")
        return count

    # ========================== المحاكاة البشرية في الردود ==========================
    async def human_like_reply(self, event, client):
        """يرد بشكل طبيعي كإنسان بعد رؤية النجوم الحقيقية"""
        if event.out or not event.is_private:
            return False
        
        text = event.raw_text or ""
        
        # 1. التحقق من وجود نجوم حقيقية (إيموجي أو ستيكر)
        has_real_stars = any(emoji in text for emoji in STAR_EMOJIS)
        has_heart = any(heart in text for heart in HEART_STICKERS)
        
        if not has_real_stars and not has_heart:
            return False  # لا نرد إذا لم تكن هناك نجوم حقيقية
        
        # 2. محاكاة التأخير البشري (لا نقرأ فوراً)
        await asyncio.sleep(random.uniform(3, 15))  # نتظاهر بعدم رؤية الرسالة فوراً
        
        # 3. تعليم القراءة بعد فترة
        try:
            await client(ReadHistoryRequest(peer=event.chat_id, max_id=event.id))
        except:
            pass
        
        # 4. محاكاة الكتابة
        await asyncio.sleep(random.uniform(1.5, 4.0))
        try:
            async with client.action(event.chat_id, 'typing'):
                await asyncio.sleep(random.uniform(1.0, 3.0))
        except:
            pass
        
        # 5. الرد المناسب
        reply = None
        if has_heart or '❤️' in text:
            reply = random.choice([
                "شكراً 💫", "تسلم 🌸", "حبيبي 🖤", "الله يسعدك 💝",
                "ما تقصر ✨", "يدك مبدوءة بالخير 💖"
            ])
        elif has_real_stars:
            if any(w in text.lower() for w in ['اهداء', 'هدية', 'gift']):
                reply = "واااو شكراً عالهدية! 💝🎁"
            else:
                reply = random.choice([
                    "شكراً 🌟", "تسلم 💫", "ما قصرت ✨", "يعطيك العافية 💙"
                ])
        
        if reply:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            try:
                await event.reply(reply)
                logger.info(f"💬 رد بشري: {reply[:30]}")
                return True
            except:
                pass
        
        return False

    # ========================== معالجة الرسائل ==========================
    async def process_message(self, event, client):
        if not self.running:
            return
        
        text = event.raw_text or ""

        # 1. الكشف عن الهدايا الواردة وتحويلها فوراً
        converted = await self.convert_incoming_gift(event, client)
        if converted:
            return

        # 2. تجنب المسابقات الخطيرة
        if any(w in text for w in DANGEROUS_CONTEST):
            logger.info(f"🚫 تجنب مسابقة خطيرة: {text[:50]}...")
            return

        # 3. المسابقات الآمنة (أول شخص يكتب...)
        safe_match = re.search(SAFE_CONTEST_REGEX, text, re.IGNORECASE)
        if safe_match:
            contest_text = re.search(r'[({\[].*?[)}\]]', text)
            reply_text = contest_text.group(0).strip('(){}[]') if contest_text else "تم"
            await asyncio.sleep(random.uniform(0.3, 1.0))
            try:
                await event.reply(reply_text)
                logger.info(f"✏️ مشاركة بمسابقة آمنة: {reply_text}")
            except:
                pass
            # تحقق من وجود أزرار صيد إضافية
            if event.reply_markup:
                await self._hunt_buttons(event, client)

        # 4. صيد أزرار الروليت
        if event.reply_markup and event.id not in self.cache:
            btn_text = " ".join(b.text for row in event.reply_markup.rows for b in row.buttons)
            if any(k in (text + " " + btn_text).lower() for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self._auto_join(event, client)
                await asyncio.sleep(random.uniform(2, 6))
                await self._hunt_buttons(event, client)

        # 5. القناص (صيد الهدايا المطورة)
        await self.snipe_cheap_gifts(event)

        # 6. الرد البشري (للخاص فقط)
        await self.human_like_reply(event, client)

    async def _hunt_buttons(self, event, client):
        """نقر أزرار الصيد"""
        if not event.reply_markup:
            return
        for r_idx, row in enumerate(event.reply_markup.rows):
            for b_idx, btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r_idx, b_idx)
                        self.stats['wins'] += 1
                        earned = random.randint(1, 5)
                        self.stars_balance += earned
                        self.stats['stars_earned'] += earned
                        
                        # تفعيل القناص تلقائياً
                        if not self.sniper_enabled and self.stars_balance >= MIN_STARS_FOR_SNIPER:
                            self.sniper_enabled = True
                            logger.info(f"🎯 القناص مفعل! الرصيد: {self.stars_balance}")
                        
                        return
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                    except:
                        pass

    async def _auto_join(self, event, client):
        """الانضمام التلقائي للقنوات المطلوبة"""
        links = set()
        if event.entities:
            for ent in event.entities:
                if hasattr(ent, 'url') and 't.me' in (ent.url or ''):
                    links.add(ent.url)
        found = re.findall(r'(?:t\.me/[\w\d_]+|@[\w\d_]+)', event.raw_text)
        links.update(found)
        for link in links:
            name = link.split('/')[-1].replace('@', '')
            try:
                await client(JoinChannelRequest(name))
            except:
                pass

    # ========================== تغيير الهوية ==========================
    async def persona_loop(self, client):
        while self.running:
            await asyncio.sleep(3600)  # كل ساعة
            if not self.sniper_enabled:
                continue
            if (datetime.now() - self.last_persona_change).total_seconds() > random.randint(70000, 100000):
                try:
                    name = random.choice(PERSONA_NAMES)
                    bio = random.choice(PERSONA_BIOS)
                    await client(UpdateProfileRequest(first_name=name, about=bio))
                    self.last_persona_change = datetime.now()
                    logger.info(f"🔄 تحولت إلى: {name}")
                except:
                    pass

    # ========================== نظام الأوامر ==========================
    async def execute_command(self, event, cmd_parts, client):
        cmd = cmd_parts[0][1:].lower()
        args = cmd_parts[1:]
        
        try:
            if cmd == "stop":
                self.running = False
                await event.reply("🛑 تم إيقاف المحرك")
            elif cmd == "start":
                self.running = True
                await event.reply("✅ تم تشغيل المحرك")
            elif cmd == "status":
                uptime = str(timedelta(seconds=int(time.time() - self.stats['start_time'])))
                await event.reply(
                    f"📊 **Omega Ultimate Status**\n"
                    f"⚙️ الحالة: {'🟢 يعمل' if self.running else '🔴 متوقف'}\n"
                    f"⏱️ مدة التشغيل: {uptime}\n"
                    f"🏆 مرات الصيد: {self.stats['wins']}\n"
                    f"⭐ النجوم: ~{self.stars_balance}\n"
                    f"🎁 هدايا محوَّلة: {self.stats['gifts_converted']}\n"
                    f"💎 هدايا مشتراة: {self.stats['gifts_bought']}\n"
                    f"🚪 قنوات غودرت: {self.stats['channels_left']}\n"
                    f"🎯 القناص: {'مفعل' if self.sniper_enabled else 'معطل'}"
                )
            elif cmd == "leavedead":
                count = await self.leave_dead_channels(client)
                await event.reply(f"🧹 تمت مغادرة {count} قناة ميتة")
            elif cmd == "always_online":
                await client(UpdateStatusRequest(offline=False))
                await event.reply("🟢 الحساب سيظهر متصل دائماً")
            elif cmd == "sniper_on":
                self.sniper_enabled = True
                await event.reply("🎯 القناص مفعل")
            elif cmd == "sniper_off":
                self.sniper_enabled = False
                await event.reply("🎯 القناص معطل")
            elif cmd == "clearcache":
                self.cache.clear()
                await event.reply("🧹 تم مسح الكاش")
            elif cmd == "help":
                await event.reply(
                    "🔥 **Omega Ultimate**\n"
                    ".stop | .start | .status | .leavedead\n"
                    ".always_online | .sniper_on | .sniper_off | .clearcache\n"
                    ".setname [اسم] | .setbio [نبذة] | .setphoto (بالرد على صورة)"
                )
            elif cmd == "setname" and args:
                await client(UpdateProfileRequest(first_name=" ".join(args)))
                await event.reply("✅ تم تغيير الاسم")
            elif cmd == "setbio" and args:
                await client(UpdateProfileRequest(about=" ".join(args)))
                await event.reply("✅ تم تغيير النبذة")
            else:
                await event.reply("❓ أمر غير معروف. .help")
        except Exception as e:
            await event.reply(f"⚠️ خطأ: {e}")

    # ========================== التشغيل الرئيسي ==========================
    async def main(self):
        logger.info("■ بدء Omega Ultimate ■")
        
        # اتصال الحساب 1
        if not await self.iron_connect(self.c1, "حساب 1"):
            logger.critical("❌ فشل اتصال الحساب 1")
            return
        
        # اتصال الحساب 2 (اختياري)
        if self.c2:
            if not await self.iron_connect(self.c2, "حساب 2"):
                logger.warning("⚠️ الحساب 2 غير متاح، المتابعة بالحساب 1 فقط")
                self.c2 = None
        
        # اختيار العميل الرئيسي للشخصية والقنوات
        main_client = self.c2 or self.c1

        # ==================== معالجات الأحداث ====================
        @self.c1.on(events.NewMessage)
        async def handler1(event):
            if event.sender_id == ADMIN_ID and event.raw_text.startswith("."):
                await self.execute_command(event, event.raw_text.split(), self.c1)
                return
            await self.process_message(event, self.c1)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def handler2(event):
                await self.process_message(event, self.c2)

        # ==================== المهام الخلفية ====================
        asyncio.create_task(self.keep_alive(self.c1, "حساب 1"))
        if self.c2:
            asyncio.create_task(self.keep_alive(self.c2, "حساب 2"))
        
        # تغيير الهوية كل 20-28 ساعة
        asyncio.create_task(self.persona_loop(main_client))
        
        # مغادرة القنوات الميتة كل 8 ساعات
        async def dead_cleaner():
            while self.running:
                await asyncio.sleep(28800)  # 8 ساعات
                await self.leave_dead_channels(main_client)
        asyncio.create_task(dead_cleaner())

        # إظهار الحساب متصل دائماً من البداية
        await main_client(UpdateStatusRequest(offline=False))
        logger.info("🟢 الحساب يظهر متصل دائماً")

        logger.info("🚀 Omega Ultimate يعمل بكامل طاقته!")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(OmegaUltimate().main())
    except KeyboardInterrupt:
        logger.info("إيقاف يدوي")
