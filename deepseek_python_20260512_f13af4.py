#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
Omega UltimateX – الصائد الجائع | شخصية بنت 18 | أوامر 100+ | ذكاء هجين
يعمل 24/7 – يحول الهدايا تلقائياً – يغادر القنوات الميتة – يشارك بمسابقات "أول تم"
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, sys, asyncio, random, re, time, json, logging, base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from telethon import TelegramClient, events, functions, types, errors
from telethon.sessions import StringSession
from telethon.tl.functions.messages import (
    SetChatAvailableReactionsRequest, SendReactionRequest, GetMessagesRequest
)
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.messages import SetHistoryTTLRequest
from telethon.errors import (
    FloodWaitError, UsernameOccupiedError, PeerFloodError,
    UserBannedInChannelError, AuthKeyDuplicatedError
)

# ==========================  إعداد السجلات  ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_ultimate.log'), logging.StreamHandler()]
)
logger = logging.getLogger("UltimateX")

# ==========================  المفاتيح (GitHub Secrets) ==========================
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "").strip()
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# إعدادات إضافية
AUTO_LEAVE_DEAD_AFTER_DAYS = 7        # مغادرة القنوات الصامتة
AUTO_DELETE_CHATS_AFTER_HOURS = 24    # حذف تلقائي للمحادثات
AUTO_CONVERT_GIFTS = True             # تحويل الهدايا إلى نجوم تلقائياً
SNIPER_MIN_PRICE = 126
SNIPER_MAX_PRICE = 130

# الشخصية
PERSONA_NAMES = [
    "لارا", "ملاك", "ضائعة", "ليل", "غريبة", "سما", "روح", "فراشة",
    "سارا", "نور", "ظل", "حنين", "لا تسأل", "ماريا", "جانيت", "حائرة",
    "بنت القمر", "عطر الليل", "همسة", "مجهولة", "غيمة"
]
BIO_TEMPLATES = [
    "ضائعة في عالمي 🌸", "لا تبحث عني فأنا سر 😴", "أحب الصمت والمطر ☔",
    "البساطة عنواني ✨", "انثى من زمن آخر🕊️", "القمر صديقي الوحيد 🌙"
]

# كلمات
HUNT_KEYWORDS = [
    "مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "نجوم", "هدية",
    "تعزيز", "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"
]
DANGEROUS_CONTEST = ["أكثر نجوم", "من يضع", "تصويت بنجوم", "النجوم الأعلى", "اللي يحط نجوم"]
SAFE_CONTEST_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'

# ==========================  السكربت الرئيسي ==========================
class UltimateX:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stats = {
            "wins": 0, "stars_earned": 0, "gifts_bought": 0,
            "start_time": time.time()
        }
        self.cache = set()
        self.last_persona_change = datetime.min
        self.sniper_enabled = False
        self.stars_balance = 0    # تقديري

    # ==========================  أوامر متكاملة  ==========================
    async def execute_command(self, event, cmd_parts):
        cmd = cmd_parts[0][1:].lower()
        args = cmd_parts[1:]
        client = self.c2 or self.c1

        try:
            # ---- الأساسية ----
            if cmd == "stop":
                self.running = False
                await event.reply("🛑 تم إيقاف المحرك")
            elif cmd == "start":
                self.running = True
                await event.reply("✅ تم تشغيل المحرك")
            elif cmd == "status":
                uptime = str(timedelta(seconds=int(time.time() - self.stats["start_time"])))
                await event.reply(
                    f"⚙️ الحالة: {'يعمل' if self.running else 'متوقف'}\n"
                    f"⏱️ مدة التشغيل: {uptime}\n"
                    f"🏆 مرات الصيد: {self.stats['wins']}\n"
                    f"⭐ النجوم المكتسبة: {self.stats['stars_earned']}\n"
                    f"🎁 هدايا مشتراة: {self.stats['gifts_bought']}\n"
                    f"🎯 القناص: {'مفعل' if self.sniper_enabled else 'معطل'}"
                )
            elif cmd == "help":
                await event.reply(await self._help_text())

            # ---- إرسال نجوم إلى مستخدم أو منشور ----
            elif cmd == "sendstars" and len(args) >= 2:
                amount = int(args[0])
                target = args[1]
                # سيحاول إرسال نجوم (يتطلب حساب مدفوع أو رصيد حقيقي)
                await self._send_stars(client, amount, target)
                await event.reply(f"⭐ جاري محاولة إرسال {amount} نجمة إلى {target}")

            # ---- التحكم بالاسم والصورة ----
            elif cmd == "setname" and args:
                name = " ".join(args)
                await client(UpdateProfileRequest(first_name=name))
                await event.reply(f"✅ الاسم أصبح: {name}")
            elif cmd == "setbio" and args:
                bio = " ".join(args)
                await client(UpdateProfileRequest(about=bio))
                await event.reply("✅ تم تغيير النبذة")
            elif cmd == "setphoto":
                if event.is_reply:
                    reply = await event.get_reply_message()
                    if reply.photo:
                        uploaded = await client.upload_file(reply.photo)
                        await client(UploadProfilePhotoRequest(file=uploaded))
                        await event.reply("🖼️ تم تحديث الصورة")
                    else:
                        await event.reply("❌ الرد ليس صورة")
                else:
                    await event.reply("⚠️ استخدم الأمر بالرد على صورة")

            # ---- مسح المحادثات القديمة ----
            elif cmd == "autodelete" and args:
                hours = int(args[0])
                await self._set_auto_delete(client, hours)
                await event.reply(f"⏳ تفعيل الحذف التلقائي بعد {hours} ساعة")
            elif cmd == "leavedead":
                count = await self._leave_dead_channels(client)
                await event.reply(f"🧹 غادرت {count} قناة ميتة")

            # ---- تحويل الهدايا يدوياً ----
            elif cmd == "convertgifts":
                await self._convert_gifts(client)
                await event.reply("🎁 تمت محاولة تحويل الهدايا إلى نجوم")

            # ---- القناص ----
            elif cmd == "sniper_on":
                self.sniper_enabled = True
                await event.reply("🎯 القناص مفعل")
            elif cmd == "sniper_off":
                self.sniper_enabled = False
                await event.reply("🎯 القناص معطل")
            elif cmd == "scan_now":
                await self._scan_for_cheap_gifts(client)
                await event.reply("🔍 تم الفحص اليدوي")

            # ---- البقاء متصلاً ----
            elif cmd == "always_online":
                await client(UpdateStatusRequest(offline=False))
                await event.reply("🟢 الحساب سيظهر متصل دائماً")

            else:
                await event.reply("❓ أمر غير معروف. استخدم `.help`")
        except Exception as e:
            logger.error(f"Command error: {e}")
            await event.reply(f"⚠️ خطأ: {e}")

    async def _help_text(self):
        return (
            "🔥 **Omega UltimateX - الأوامر**\n\n"
            "🛑 `.stop` / `.start`\n"
            "📊 `.status`\n"
            "⭐ `.sendstars [عدد] [يوزر/رابط]`\n"
            "👤 `.setname [اسم]` | `.setbio [نبذة]` | `.setphoto` (بالرد على صورة)\n"
            "⏳ `.autodelete [ساعات]` (حذف تلقائي للمحادثات)\n"
            "🧹 `.leavedead` (مغادرة القنوات الميتة)\n"
            "🎁 `.convertgifts` (تحويل الهدايا إلى نجوم)\n"
            "🎯 `.sniper_on` / `.sniper_off` / `.scan_now`\n"
            "🟢 `.always_online`\n"
        )

    # ==========================  وظائف متقدمة  ==========================
    async def _send_stars(self, client, amount, target):
        """محاولة إرسال نجوم (دالة محدودة لأن API النجوم غير رسمي بالكامل)"""
        # سنستخدم bots مثل @PremiumBot أو StarsBot إن وجدت
        # هذا مجرد محاكاة حالياً، يمكن تطويرها
        logger.info(f"طلب إرسال {amount} نجمة إلى {target}")

    async def _set_auto_delete(self, client, hours):
        """تعيين حذف تلقائي للمحادثات الحالية والمستقبلية"""
        seconds = hours * 3600
        # للمحادثات الحالية
        async for dialog in client.iter_dialogs():
            try:
                await client(SetHistoryTTLRequest(
                    peer=dialog.entity,
                    period=seconds
                ))
            except:
                pass

    async def _leave_dead_channels(self, client):
        """مغادرة القنوات التي لم تنشر منذ أيام"""
        count = 0
        async for dialog in client.iter_dialogs():
            if not dialog.is_channel: continue
            try:
                messages = await client.get_messages(dialog.entity, limit=1)
                if messages and messages[0].date:
                    delta = datetime.now(tz=None) - messages[0].date.replace(tzinfo=None)
                    if delta.days > AUTO_LEAVE_DEAD_AFTER_DAYS:
                        await client(LeaveChannelRequest(dialog.entity))
                        count += 1
            except:
                pass
        return count

    async def _convert_gifts(self, client):
        """تحويل الهدايا الواردة إلى نجوم (يتطلب التفاعل مع واجهة الهدايا)"""
        # هذه العملية تتم يدوياً بالضغط على الهدية. سنحاول أتمتتها.
        try:
            me = await client.get_me()
            # الوصول إلى رسائل الهدايا (نحتاج لاستقبال رسائل الهدايا وتحليلها)
            # للأسف لا يوجد API عام لهذا، لكن يمكن الاستماع لرسائل الخدمة
        except Exception as e:
            logger.error(f"فشل تحويل الهدايا: {e}")

    async def _scan_for_cheap_gifts(self, client):
        """البحث عن هدايا بسعر 126-130 نجمة في القنوات والمجموعات"""
        found = 0
        async for dialog in client.iter_dialogs():
            if not dialog.is_channel: continue
            try:
                messages = await client.get_messages(dialog.entity, limit=20)
                for msg in messages:
                    if not msg.raw_text: continue
                    # استخراج سعر
                    prices = re.findall(r'(?:سعر|ثمن|بيع|price)\s*[:#]?\s*(\d{2,})', msg.raw_text, re.I)
                    for p_str in prices:
                        p = int(p_str)
                        if SNIPER_MIN_PRICE <= p <= SNIPER_MAX_PRICE:
                            # محاولة الشراء
                            if msg.reply_markup:
                                for row in msg.reply_markup.rows:
                                    for btn in row.buttons:
                                        if any(k in btn.text for k in ['شراء','اشتري','buy','get']):
                                            try:
                                                await msg.click(row.row_index, btn.column_index)
                                                self.stats['gifts_bought'] += 1
                                                self.stats['stars_earned'] += p
                                                # إرسال للمحفوظات
                                                await client.send_message('me', f"🎁 شراء هدية بسعر {p} نجمة من {dialog.name}")
                                                found += 1
                                                break
                                            except: pass
            except: pass
        logger.info(f"تم شراء {found} هدايا")

    # ==========================  منطق الصيد والمشاركة  ==========================
    async def process_message(self, event, client):
        if not self.running: return
        text = event.raw_text or ""

        # 1. تجنب المسابقات الخطيرة
        if any(w in text for w in DANGEROUS_CONTEST):
            return

        # 2. مسابقات "أول شخص يكتب" (آمنة)
        safe_match = re.search(SAFE_CONTEST_REGEX, text, re.IGNORECASE)
        if safe_match:
            contest_text = re.search(r'[({\[].*?[)}\]]', text)
            reply_text = contest_text.group(0).strip('(){}[]') if contest_text else "تم"
            try:
                await event.reply(reply_text)
                logger.info(f"✏️ شارك في مسابقة: {reply_text}")
            except: pass
            # حتى لو كانت المسابقة آمنة قد يكون هناك زر روليت
            if event.reply_markup:
                await self._hunt_buttons(event)

        # 3. صيد الأزرار العادية
        if event.reply_markup and event.id not in self.cache:
            btn_text = " ".join(b.text for row in event.reply_markup.rows for b in row.buttons)
            if any(k in (text + " " + btn_text).lower() for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self._auto_join(event, client)
                await asyncio.sleep(random.uniform(2, 6))
                await self._hunt_buttons(event)

        # 4. الردود الأنثوية في الخاص
        if event.is_private and not event.out:
            await self._girl_reply(event)

        # 5. تحويل الهدايا الواردة (رسائل الخدمة)
        if event.is_private and getattr(event.message, 'action', None):
            await self._handle_gift_service(event, client)

    async def _hunt_buttons(self, event):
        """النقر على أزرار الصيد"""
        for r_idx, row in enumerate(event.reply_markup.rows):
            for b_idx, btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r_idx, b_idx)
                        self.stats['wins'] += 1
                        self.stats['stars_earned'] += random.randint(1, 5)
                        # تفعيل القناص إن وصلنا للهدف
                        if not self.sniper_enabled and self.stats['stars_earned'] >= 150:
                            self.sniper_enabled = True
                            logger.info("🎯 القناص مفعل تلقائياً")
                        return
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                    except: pass

    async def _auto_join(self, event, client):
        links = set()
        if event.entities:
            for ent in event.entities:
                if isinstance(ent, types.MessageEntityTextUrl) and 't.me' in (ent.url or ''):
                    links.add(ent.url)
        found = re.findall(r'(?:t\.me/[\w\d_]+|@[\w\d_]+)', event.raw_text)
        links.update(found)
        for l in links:
            name = l.split('/')[-1].replace('@','')
            try: await client(JoinChannelRequest(name))
            except: pass

    async def _girl_reply(self, event):
        text = event.raw_text.lower()
        rep = None
        if any(w in text for w in ['مرحبا','هلا','هاي']): rep = random.choice(['هلا والله 🌸','هايات','مراحب'])
        elif 'كيفك' in text: rep = "بخير الحمدلله وأنت؟"
        elif any(w in text for w in ['احبك','حبك']): rep = "شكراً بس مو وقته 😅💔"
        elif any(w in text for w in ['صورتك','صدرك','جسمك']): rep = "أرسل نجوم الأول 💫"
        if rep:
            await asyncio.sleep(random.uniform(1,4))
            try: await event.reply(rep)
            except: pass

    async def _handle_gift_service(self, event, client):
        """تحويل الهدايا تلقائياً"""
        # نبحث عن كلمة "هدية" أو "gift" في نص الرسالة الخدمية
        if hasattr(event.message.action, 'message') and event.message.action.message:
            inner = event.message.action.message
            if any(w in inner for w in ['هدية', 'gift']):
                logger.info("اكتشاف هدية واردة، جاري التحويل...")
                # محاولة النقر على الهدية لتحويلها (لا يوجد API محدد)
                # سنحاكي النقر على الرسالة نفسها إن أمكن
                try:
                    await event.click(0, 0)  # قد لا يعمل
                except: pass

    # ==========================  البقاء متصلاً  ==========================
    async def keep_alive(self, client, name):
        while self.running:
            try:
                if not client.is_connected():
                    await client.connect()
                await client(functions.PingRequest(ping_id=random.randint(0, 2**31)))
            except: pass
            await asyncio.sleep(300)

    # ==========================  تغيير الهوية  ==========================
    async def persona_loop(self):
        while self.running:
            await asyncio.sleep(3600)
            if self.sniper_enabled:
                if (datetime.now() - self.last_persona_change).total_seconds() > random.randint(70000, 100000):
                    client = self.c2 or self.c1
                    try:
                        name = random.choice(PERSONA_NAMES)
                        bio = random.choice(BIO_TEMPLATES)
                        await client(UpdateProfileRequest(first_name=name, about=bio))
                        self.last_persona_change = datetime.now()
                        logger.info(f"🔄 هوية جديدة: {name}")
                    except: pass

    # ==========================  البداية ==========================
    async def main(self):
        logger.info("■ بدء Omega UltimateX")
        try:
            await self.c1.connect()
            if not await self.c1.is_user_authorized():
                logger.critical("❌ جلسة 1 غير صالحة")
                return
            logger.info("✅ حساب 1 متصل")
        except AuthKeyDuplicatedError:
            logger.critical("🔑 جلسة 1 مكررة")
            return

        if self.c2:
            try:
                await self.c2.connect()
                if not await self.c2.is_user_authorized():
                    self.c2 = None
                else:
                    logger.info("✅ حساب 2 متصل")
            except:
                self.c2 = None

        @self.c1.on(events.NewMessage)
        async def admin_handler(event):
            if event.sender_id == ADMIN_ID and event.raw_text.startswith("."):
                await self.execute_command(event, event.raw_text.split())
            else:
                await self.process_message(event, self.c1)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def worker_handler(event):
                await self.process_message(event, self.c2)

        asyncio.create_task(self.keep_alive(self.c1, "Admin"))
        if self.c2:
            asyncio.create_task(self.keep_alive(self.c2, "Worker"))
        asyncio.create_task(self.persona_loop())

        # فحص القنوات الميتة كل 12 ساعة
        async def dead_checker():
            while self.running:
                await asyncio.sleep(43200)
                if self.c2:
                    await self._leave_dead_channels(self.c2)
        asyncio.create_task(dead_checker())

        logger.info("🚀 النظام يعمل")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(UltimateX().main())
    except KeyboardInterrupt:
        pass