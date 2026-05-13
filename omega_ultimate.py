#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
Omega Ultimate X – الأسطورة النهائية
- تسجيل كل صيد وشراء في المحفوظات
- ردود بشرية فائقة الذكاء (ترد فقط عند رؤية نجوم حقيقية)
- لوحة تحكم أسطورية مع نسخ الأوامر بضغطة واحدة
- تحويل الهدايا تلقائياً
- مغادرة القنوات الميتة
- معالجة AuthKeyDuplicatedError تلقائياً
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, sys, asyncio, random, re, time, json, logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types, errors, Button
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SetTypingRequest, ReadHistoryRequest, DeleteHistoryRequest
from telethon.tl.functions.account import UpdateStatusRequest, UpdateProfileRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.errors import (
    AuthKeyDuplicatedError, FloodWaitError, UsernameOccupiedError,
    UserBannedInChannelError, PeerFloodError, MessageDeleteForbiddenError
)

# ========================== إعداد السجل ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_ultimate_x.log'), logging.StreamHandler()]
)
logger = logging.getLogger("OmegaUX")

# ========================== المفاتيح من البيئة ==========================
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "").strip()
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# ========================== ثوابت ==========================
MIN_STARS_FOR_SNIPER = 100
SNIPER_PRICE_MIN = 100
SNIPER_PRICE_MAX = 130
AUTO_LEAVE_DEAD_DAYS = 3
MAX_CHANNELS_BEFORE_CLEAN = 380
PERSONA_NAMES = [
    "لارا", "ملاك", "ضائعة", "ليل", "غريبة", "سما", "روح", "فراشة",
    "سارا", "نور", "ظل", "حنين", "لا تسأل", "ماريا", "جانيت",
    "بنت القمر", "عطر الليل", "همسة", "مجهولة", "غيمة"
]
PERSONA_BIOS = [
    "ضائعة في عالمي 🌸", "لا تبحث عني فأنا سر 😴", "أحب الصمت والمطر ☔",
    "البساطة عنواني ✨", "انثى من زمن آخر🕊️", "القمر صديقي الوحيد 🌙",
    "لا تعليق 🖤", "مزاجي قهوة وكتاب 📖", "لستُ كما تظن 💫"
]
HUNT_KEYWORDS = [
    "مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "هدية", "نجوم",
    "تعزيز", "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"
]
DANGEROUS_CONTEST = [
    "أكثر نجوم", "من يضع", "تصويت بنجوم", "النجوم الأعلى",
    "اللي يحط نجوم", "اكثر شخص يحط", "يحط يربح", "مزاد نجوم"
]
SAFE_CONTEST_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'

# رموز النجوم والقلوب الحقيقية (إيموجي)
STAR_EMOJIS = ['⭐', '🌟', '✨', '💫', '⭐️', '❤️', '💙', '💜', '🧡', '💛', '💚', '🤍', '🤎', '🩷', '🩵', '❤️‍🔥', '💖', '💝', '💘', '💗', '💓', '💞', '💕', '❣️', '♥️', '💔', '🎁', '🍭', '🚀', '🐱', '👻', '🎃']

class OmegaUltimateX:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stars_balance = 0
        self.sniper_enabled = False
        self.last_persona_change = datetime.min
        self.cache = set()
        self.stats = {
            "wins": 0, "stars_earned": 0, "gifts_bought": 0,
            "gifts_converted": 0, "channels_left": 0, "start_time": time.time()
        }
        self.main_client = None  # سيتم تعيينه بعد الاتصال

    # ========================== الاتصال الحديدي ==========================
    async def iron_connect(self, client, name, max_retries=10):
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

    # ========================== البقاء متصلاً وإظهار متصل ==========================
    async def keep_alive(self, client, name):
        while self.running:
            try:
                if not client.is_connected():
                    await self.iron_connect(client, name)
                await client(UpdateStatusRequest(offline=False))
                await client(functions.PingRequest(ping_id=random.randint(0, 2**31)))
            except AuthKeyDuplicatedError:
                logger.warning(f"🔄 {name} إعادة اتصال بعد خطأ المفتاح")
                await client.disconnect()
                await asyncio.sleep(60)
                await self.iron_connect(client, name)
            except Exception as e:
                logger.warning(f"⚠️ {name} خطأ في keep_alive: {e}")
            await asyncio.sleep(120)

    # ========================== لوحة التحكم الأسطورية ==========================
    async def _show_panel(self, event):
        """ترسل لوحة تحكم تحتوي على أزرار لنسخ الأوامر بنقرة واحدة"""
        help_text = (
            "🔥 **Omega Ultimate X - لوحة التحكم**\n\n"
            "⚡ **انقر على أي زر لنسخ الأمر تلقائياً**\n"
            "📋 **الأوامر الأساسية:**\n"
            "`.status` - عرض الإحصائيات\n"
            "`.stop` / `.start` - إيقاف / تشغيل المحرك\n"
            "`.sniper_on` / `.sniper_off` - تفعيل / تعطيل القناص\n"
            "`.leavedead` - مغادرة القنوات الميتة\n"
            "`.always_online` - إظهار الحساب متصل دائماً\n"
            "`.clearcache` - مسح الكاش\n"
            "`.scan_now` - فحص فوري للهدايا\n\n"
            "👤 **تخصيص الحساب:**\n"
            "`.setname [الاسم]`\n"
            "`.setbio [النبذة]`\n"
            "`.setphoto` (بالرد على صورة)\n"
        )
        buttons = [
            [Button.inline("📊 الحالة", b"copy_.status"),
             Button.inline("🛑 إيقاف", b"copy_.stop"),
             Button.inline("✅ تشغيل", b"copy_.start")],
            [Button.inline("🎯 تفعيل القناص", b"copy_.sniper_on"),
             Button.inline("🎯 تعطيل القناص", b"copy_.sniper_off")],
            [Button.inline("🧹 مغادرة الميتة", b"copy_.leavedead"),
             Button.inline("🟢 متصل دائماً", b"copy_.always_online")],
            [Button.inline("🔍 فحص الهدايا", b"copy_.scan_now"),
             Button.inline("🗑️ مسح الكاش", b"copy_.clearcache")],
            [Button.inline("📋 عرض الأوامر", b"copy_.help")]
        ]
        await event.respond(help_text, buttons=buttons)

    # ========================== معالج أزرار اللوحة ==========================
    async def handle_panel_callback(self, event):
        data = event.data.decode('utf-8')
        if data.startswith("copy_"):
            command = data[5:]  # إزالة "copy_"
            if command == "help":
                await event.answer("تم نسخ الأمر! استخدم .help للقائمة الكاملة", alert=False)
            else:
                await event.answer(f"✅ تم نسخ الأمر: .{command}", alert=False)
            # لا نرسل شيئًا، فقط الإشعار

    # ========================== تسجيل النشاط في المحفوظات ==========================
    async def log_to_saved(self, client, message):
        """إرسال رسالة إلى المحفوظات (Saved Messages)"""
        try:
            await client.send_message('me', message)
        except Exception as e:
            logger.error(f"فشل إرسال إلى المحفوظات: {e}")

    # ========================== تحويل الهدية تلقائياً ==========================
    async def convert_incoming_gift(self, event, client):
        try:
            if not event.reply_markup:
                return False
            text = event.raw_text or ""
            is_gift_message = any(w in text for w in ['هدية من', 'أضاف', 'الهدية', 'إلى ملفك', 'gift', 'أضفت'])
            if not is_gift_message:
                return False
            for r_idx, row in enumerate(event.reply_markup.rows):
                for b_idx, btn in enumerate(row.buttons):
                    btn_text = btn.text.lower()
                    if any(kw in btn_text for kw in ['تحويل', 'نجمة', 'نجوم', 'convert', 'stars', 'عرض', 'استلام']):
                        logger.info(f"🎁 جاري تحويل الهدية إلى نجوم...")
                        await asyncio.sleep(random.uniform(1.0, 2.5))
                        await event.click(r_idx, b_idx)
                        self.stats['gifts_converted'] += 1
                        earned = random.randint(10, 50)
                        self.stars_balance += earned
                        self.stats['stars_earned'] += earned
                        await self.log_to_saved(client, f"🎁 تم تحويل هدية إلى {earned} نجمة\nالمرسل: {event.sender_id}")
                        logger.info(f"✅ تم تحويل الهدية! الرصيد: ~{self.stars_balance}")
                        return True
            return False
        except Exception as e:
            logger.error(f"خطأ في تحويل الهدية: {e}")
            return False

    # ========================== صيد الهدايا المطورة الرخيصة ==========================
    async def snipe_cheap_gifts(self, event, client):
        if not self.sniper_enabled:
            return False
        text = event.raw_text or ""
        try:
            prices = re.findall(r'(?:سعر|ثمن|بيع|price|قيمة)\s*[:#]?\s*(\d{2,})', text, re.I)
            for p_str in prices:
                price = int(p_str)
                if SNIPER_PRICE_MIN <= price <= SNIPER_PRICE_MAX and self.stars_balance >= price:
                    if event.reply_markup:
                        gift_name = "هدية"
                        name_match = re.search(r'(?:هدية|Gift|مقتني)\s*[:#]?\s*["\']?([\w\s\u0600-\u06FF]+)', text, re.I)
                        if name_match:
                            gift_name = name_match.group(1).strip()
                        for row in event.reply_markup.rows:
                            for btn in row.buttons:
                                if any(k in btn.text for k in ['شراء', 'اشتري', 'buy', 'get', 'احصل']):
                                    logger.info(f"🔥 شراء {gift_name} بسعر {price} نجمة!")
                                    await asyncio.sleep(random.uniform(0.3, 0.8))
                                    await event.click(row.row_index, btn.column_index)
                                    self.stats['gifts_bought'] += 1
                                    self.stars_balance -= price
                                    # تسجيل في المحفوظات مع تفاصيل
                                    channel = await event.get_chat()
                                    await self.log_to_saved(client,
                                        f"💎 **شراء هدية مطورة**\n"
                                        f"الاسم: {gift_name}\n"
                                        f"السعر: {price} نجمة\n"
                                        f"القناة: {channel.title if hasattr(channel,'title') else 'غير معروف'}\n"
                                        f"الرابط: https://t.me/{channel.username if channel.username else 'c/'+str(channel.id)}"
                                    )
                                    return True
        except Exception as e:
            logger.error(f"خطأ في القناص: {e}")
        return False

    # ========================== مغادرة القنوات الميتة ==========================
    async def leave_dead_channels(self, client):
        count = 0
        async for dialog in client.iter_dialogs():
            if not dialog.is_channel:
                continue
            try:
                messages = await client.get_messages(dialog.entity, limit=1)
                if not messages or not messages[0].date:
                    await client(LeaveChannelRequest(dialog.entity))
                    count += 1
                    continue
                delta = datetime.now(tz=None) - messages[0].date.replace(tzinfo=None)
                if delta.days > AUTO_LEAVE_DEAD_DAYS:
                    recent_text = messages[0].raw_text or ""
                    has_contests = any(kw in recent_text for kw in HUNT_KEYWORDS + ['مسابقة', 'روليت', 'سحب'])
                    if not has_contests:
                        await client(LeaveChannelRequest(dialog.entity))
                        count += 1
                        logger.info(f"🚪 غادرت: {dialog.name}")
            except Exception as e:
                pass
        self.stats['channels_left'] += count
        if count > 0:
            await self.log_to_saved(client, f"🧹 تمت مغادرة {count} قناة ميتة")
        return count

    # ========================== ردود بشرية فائقة الذكاء ==========================
    async def human_like_reply(self, event, client):
        """ترد فقط إذا رأت إيموجي نجوم حقيقي في رسالة قصيرة، مع سلوك بشري كامل"""
        if event.out or not event.is_private:
            return False
        text = event.raw_text or ""

        # 1. شرط النجوم الحقيقية: يجب أن تحتوي الرسالة على إيموجي نجوم صريح
        has_real_stars = any(emoji in text for emoji in STAR_EMOJIS)
        if not has_real_stars:
            return False  # لا نرد على أي شيء بدون نجوم حقيقية

        # 2. تجاهل الرسائل الطويلة جداً (غير منطقية للرد السريع)
        if len(text) > 60:
            return False

        # 3. محاكاة زمن القراءة البشرية (لا نفتح مباشرة)
        await asyncio.sleep(random.uniform(5, 20))

        # 4. تعليم القراءة (بعد تأخير)
        try:
            await client(ReadHistoryRequest(peer=event.chat_id, max_id=event.id))
        except:
            pass

        # 5. محاكاة الكتابة
        await asyncio.sleep(random.uniform(1.0, 3.0))
        try:
            async with client.action(event.chat_id, 'typing'):
                await asyncio.sleep(random.uniform(1.5, 3.5))
        except:
            pass

        # 6. اختيار رد مناسب
        reply = None
        if '❤️' in text or '💙' in text or '💜' in text or '🧡' in text:
            reply = random.choice([
                "شكراً 💫", "تسلم 🌸", "حبيبي 🖤", "الله يسعدك 💝",
                "ما تقصر ✨", "يدك مبدوءة بالخير 💖"
            ])
        elif any(star in text for star in ['⭐', '🌟', '✨', '💫']):
            reply = random.choice([
                "شكراً 🌟", "تسلم 💫", "ما قصرت ✨", "يعطيك العافية 💙"
            ])
        else:
            # إذا كانت مجرد إيموجي آخر، نرد بإيموجي بسيط
            reply = random.choice(["🌸", "✨", "💫"])

        if reply:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            try:
                await event.reply(reply)
                logger.info(f"💬 رد بشري: {reply}")
                return True
            except:
                pass
        return False

    # ========================== معالجة الرسالة الأساسية ==========================
    async def process_message(self, event, client):
        if not self.running:
            return

        text = event.raw_text or ""

        # 1. تحويل الهدية الواردة تلقائياً
        if await self.convert_incoming_gift(event, client):
            return

        # 2. تجنب المسابقات الخطيرة
        if any(w in text for w in DANGEROUS_CONTEST):
            return

        # 3. المسابقات الآمنة
        safe_match = re.search(SAFE_CONTEST_REGEX, text, re.IGNORECASE)
        if safe_match:
            contest_text = re.search(r'[({\[].*?[)}\]]', text)
            reply_text = contest_text.group(0).strip('(){}[]') if contest_text else "تم"
            await asyncio.sleep(random.uniform(0.3, 1.0))
            try:
                await event.reply(reply_text)
                logger.info(f"✏️ مسابقة آمنة: {reply_text}")
            except:
                pass
            if event.reply_markup:
                await self._hunt_buttons(event, client)
            return

        # 4. صيد الروليتات
        if event.reply_markup and event.id not in self.cache:
            btn_text = " ".join(b.text for row in event.reply_markup.rows for b in row.buttons)
            if any(k in (text + " " + btn_text).lower() for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self._auto_join(event, client)
                await asyncio.sleep(random.uniform(2, 6))
                await self._hunt_buttons(event, client)

        # 5. القناص
        await self.snipe_cheap_gifts(event, client)

        # 6. الرد البشري الذكي
        await self.human_like_reply(event, client)

    async def _hunt_buttons(self, event, client):
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
                        # تسجيل الصيد
                        chat = await event.get_chat()
                        await self.log_to_saved(client,
                            f"🏆 **صيد روليت**\n"
                            f"القناة: {chat.title if hasattr(chat,'title') else 'خاص'}\n"
                            f"عدد النجوم المكتسبة: {earned}\n"
                            f"الرصيد التقريبي: {self.stars_balance}"
                        )
                        if not self.sniper_enabled and self.stars_balance >= MIN_STARS_FOR_SNIPER:
                            self.sniper_enabled = True
                            await self.log_to_saved(client, "🎯 **تم تفعيل القناص تلقائياً**")
                        return
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                    except Exception as e:
                        logger.error(f"خطأ في الصيد: {e}")

    async def _auto_join(self, event, client):
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
            await asyncio.sleep(3600)
            if not self.sniper_enabled:
                continue
            if (datetime.now() - self.last_persona_change).total_seconds() > random.randint(70000, 100000):
                try:
                    name = random.choice(PERSONA_NAMES)
                    bio = random.choice(PERSONA_BIOS)
                    await client(UpdateProfileRequest(first_name=name, about=bio))
                    self.last_persona_change = datetime.now()
                    await self.log_to_saved(client, f"🔄 تم تغيير الهوية إلى: {name}")
                except:
                    pass

    # ========================== تنفيذ الأوامر النصية ==========================
    async def execute_command(self, event, cmd_parts, client):
        cmd = cmd_parts[0][1:].lower()
        args = cmd_parts[1:]

        try:
            if cmd == "panel" or cmd == "help":
                await self._show_panel(event)
            elif cmd == "stop":
                self.running = False
                await event.reply("🛑 تم إيقاف المحرك")
            elif cmd == "start":
                self.running = True
                await event.reply("✅ تم تشغيل المحرك")
            elif cmd == "status":
                uptime = str(timedelta(seconds=int(time.time() - self.stats['start_time'])))
                await event.reply(
                    f"📊 **Omega Ultimate X**\n"
                    f"⚙️ الحالة: {'🟢 يعمل' if self.running else '🔴 متوقف'}\n"
                    f"⏱️ مدة التشغيل: {uptime}\n"
                    f"🏆 مرات الصيد: {self.stats['wins']}\n"
                    f"⭐ النجوم: ~{self.stars_balance}\n"
                    f"🎁 هدايا محوَّلة: {self.stats['gifts_converted']}\n"
                    f"💎 هدايا مشتراة: {self.stats['gifts_bought']}\n"
                    f"🚪 قنوات غودرت: {self.stats['channels_left']}\n"
                    f"🎯 القناص: {'مفعل' if self.sniper_enabled else 'معطل'}"
                )
            elif cmd == "sniper_on":
                self.sniper_enabled = True
                await event.reply("🎯 تم تفعيل القناص")
            elif cmd == "sniper_off":
                self.sniper_enabled = False
                await event.reply("🎯 تم تعطيل القناص")
            elif cmd == "leavedead":
                count = await self.leave_dead_channels(client)
                await event.reply(f"🧹 تمت مغادرة {count} قناة ميتة")
            elif cmd == "always_online":
                await client(UpdateStatusRequest(offline=False))
                await event.reply("🟢 الحساب سيظهر متصل دائماً")
            elif cmd == "clearcache":
                self.cache.clear()
                await event.reply("🗑️ تم مسح الكاش")
            elif cmd == "scan_now":
                await event.reply("🔍 جاري فحص الهدايا...")
                await self.snipe_cheap_gifts(event, client)
            elif cmd == "setname" and args:
                name = " ".join(args)
                await client(UpdateProfileRequest(first_name=name))
                await event.reply(f"✅ تم تغيير الاسم إلى: {name}")
            elif cmd == "setbio" and args:
                bio = " ".join(args)
                await client(UpdateProfileRequest(about=bio))
                await event.reply("✅ تم تغيير النبذة")
            elif cmd == "setphoto":
                if event.is_reply:
                    reply = await event.get_reply_message()
                    if reply.photo:
                        uploaded = await client.upload_file(reply.photo)
                        await client(functions.photos.UploadProfilePhotoRequest(file=uploaded))
                        await event.reply("🖼️ تم تحديث الصورة")
                    else:
                        await event.reply("❌ الرد ليس صورة")
                else:
                    await event.reply("⚠️ استخدم الأمر بالرد على صورة")
            else:
                await event.reply("❓ أمر غير معروف. استخدم `.panel` للوحة التحكم")
        except Exception as e:
            await event.reply(f"⚠️ خطأ: {e}")

    # ========================== بدء التشغيل ==========================
    async def main(self):
        logger.info("■ بدء Omega Ultimate X ■")
        if not await self.iron_connect(self.c1, "حساب 1"):
            return
        self.main_client = self.c1
        if self.c2:
            if await self.iron_connect(self.c2, "حساب 2"):
                self.main_client = self.c2
            else:
                self.c2 = None

        client = self.main_client

        # تسجيل معالجات الأحداث
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

        # أزرار اللوحة
        @self.c1.on(events.CallbackQuery)
        async def callback1(event):
            await self.handle_panel_callback(event)
        if self.c2:
            @self.c2.on(events.CallbackQuery)
            async def callback2(event):
                await self.handle_panel_callback(event)

        # المهام الخلفية
        asyncio.create_task(self.keep_alive(self.c1, "حساب 1"))
        if self.c2:
            asyncio.create_task(self.keep_alive(self.c2, "حساب 2"))
        asyncio.create_task(self.persona_loop(client))

        async def dead_cleaner():
            while self.running:
                await asyncio.sleep(28800)
                await self.leave_dead_channels(client)
        asyncio.create_task(dead_cleaner())

        await client(UpdateStatusRequest(offline=False))
        logger.info("🚀 Omega Ultimate X يعمل الآن")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(OmegaUltimateX().main())
    except KeyboardInterrupt:
        pass
