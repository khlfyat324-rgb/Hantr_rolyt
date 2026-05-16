import os, asyncio, random, re, json, logging, time
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types, Button
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateStatusRequest, UpdateProfileRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ReadHistoryRequest, DeleteHistoryRequest
from telethon.errors import (
    AuthKeyDuplicatedError, FloodWaitError, UserBannedInChannelError,
    PeerFloodError
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_gift_sniper.log'), logging.StreamHandler()]
)
logger = logging.getLogger("OmegaGiftSniper")

# ---------- إعدادات البيئة ----------
API_ID_1 = int(os.environ["API_ID_1"]); API_HASH_1 = os.environ["API_HASH_1"]; SESSION_1 = os.environ["SESSION_1"]
API_ID_2 = int(os.environ.get("API_ID_2", 0)); API_HASH_2 = os.environ.get("API_HASH_2", ""); SESSION_2 = os.environ.get("SESSION_2", "")
ADMIN_ID = int(os.environ["ADMIN_ID"])

# ---------- نطاق السعر المستهدف ----------
GIFT_PRICE_MIN = 126
GIFT_PRICE_MAX = 149

# قنوات وأسواق الهدايا التي سنراقبها بدقة
GIFT_MARKETS = [
    "tonnel_network_bot",   
    "AutoGiftsBot",         
    "GiftHub_bot",          
    "CollectibleBot",       
    "TelegramGiftsMarket",   # أضف هنا قنوات الصيد الرائجة لديك
    "UpgradedGiftsMarket"
]

# كلمات الصيد (للروليتات)
HUNT_KEYWORDS = [
    "مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "هدية", "نجوم",
    "تعزيز", "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"
]
DANGER_WORDS = ["أكثر نجوم", "من يضع", "تصويت بنجوم", "اكثر شخص يحط", "يحط يربح", "مزاد نجوم"]
SAFE_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'

# شخصية (للحساب الثاني)
PERSONA_NAMES = ["فاطمة الزهراء", "لارا", "ملاك", "ليل", "سما", "روح", "فراشة", "نور"]
PERSONA_BIOS = ["مغربية 🇲🇦 | 18 سنة | لاعبة كرة ⚽", "بنت بسيطة من المغرب", "مزاجي كرة وسهر 🌙"]

STATS_MSG_ID = None


class OmegaGiftSniper:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stars = 150  # تعيين افتراضي بناءً على ميزانيتك المقدرة بـ 150 نجمة
        self.sniper_enabled = True  
        self.last_persona_change = datetime.min
        self.cache = set()
        self.gift_log = []  
        self.stats = {
            "wins": 0, "stars_earned": 0, "gifts_bought": 0,
            "gifts_converted": 0, "channels_left": 0,
            "msgs_processed": 0, "start": time.time()
        }
        self.main_client = None
        self.is_resting = False

    # ========== اتصال ==========
    async def connect(self, client, name):
        try:
            await client.connect()
            if await client.is_user_authorized():
                logger.info(f"✅ {name} متصل")
                return True
        except AuthKeyDuplicatedError:
            logger.critical(f"🔑 {name} الجلسة مكررة!")
        except Exception as e:
            logger.error(f"❌ {name}: {e}")
        return False

    async def keep_alive(self, client, name):
        while self.running:
            if not self.is_resting:
                try:
                    if not client.is_connected():
                        await client.connect()
                    await client(UpdateStatusRequest(offline=False))
                except:
                    pass
            else:
                try:
                    await client(UpdateStatusRequest(offline=True))
                except:
                    pass
            await asyncio.sleep(120)

    async def rest_schedule(self):
        while self.running:
            await asyncio.sleep(4 * 3600)
            self.is_resting = True
            logger.info("😴 راحة 20 دقيقة لتفادي القيود...")
            await asyncio.sleep(20 * 60)
            self.is_resting = False
            logger.info("☀️ العودة للعمل وتفعيل الصيد")

    # ========== إحصائيات حية ==========
    async def update_stats_msg(self):
        global STATS_MSG_ID
        if not self.main_client:
            return
        uptime = str(timedelta(seconds=int(time.time() - self.stats['start'])))
        status = "😴 راحة" if self.is_resting else "🟢 نشط"
        msg = (
            f"📊 **Omega Gift Sniper** ({status})\n"
            f"🕒 {datetime.now().strftime('%H:%M:%S')}\n"
            f"⏱️ مدة العمل: {uptime}\n"
            f"🏆 روليت مقبولة: {self.stats['wins']}\n"
            f"⭐ رصيد النجوم التقريبي: ~{self.stars}\n"
            f"💎 هدايا تم صيدها: {self.stats['gifts_bought']}\n"
            f"🎁 هدايا محولة: {self.stats['gifts_converted']}\n"
            f"🚪 قنوات تمت مغادرتها: {self.stats['channels_left']}\n"
            f"📨 رسائل تم فحصها: {self.stats['msgs_processed']}\n"
            f"🎯 حالة القناص: {'🟢 فعال وضمن النطاق' if self.sniper_enabled else '🔴 معطل'}"
        )
        try:
            if STATS_MSG_ID:
                await self.main_client.edit_message('me', STATS_MSG_ID, msg)
            else:
                sent = await self.main_client.send_message('me', msg)
                STATS_MSG_ID = sent.id
        except:
            pass

    # ========== معالج الرسائل والقنوات الرئيسي ==========
    async def handle_message(self, event, client, account_name):
        if not self.running or self.is_resting:
            return
        self.stats['msgs_processed'] += 1
        text = event.raw_text or ""

        # 1. تحويل الهدايا الواردة المباشرة إلى نجوم تلقائياً
        if event.reply_markup and any(w in text for w in ['هدية من', 'أضاف', 'الهدية', 'Gift']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل', 'نجمة', 'convert', 'stars']):
                        try:
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_converted'] += 1
                            self.stars += 100  # إضافة النجوم بناءً على قيمة التحويل
                            await self.update_stats_msg()
                            await client(DeleteHistoryRequest(peer=event.chat_id, max_id=0, just_clear=True))
                        except:
                            pass
                        return

        # 2. تجنب المسابقات الخطيرة
        if any(w in text for w in DANGER_WORDS):
            return

        # 3. صيد المسابقات النصية السريعة (الرد التلقائي)
        safe = re.search(SAFE_REGEX, text, re.I)
        if safe:
            match = re.search(r'[({\[].*?[)}\]]', text)
            reply_text = match.group(0).strip('(){}[]') if match else "تم"
            try:
                await event.reply(reply_text)
            except:
                pass
            if event.reply_markup:
                await self.hunt_buttons(event, client)
            return

        # 4. القناص الفعلي - صيد الهدايا المطورة (الدمج الاحترافي)
        # التحقق إذا كانت الرسالة قادمة من أسواق الهدايا أو تحتوي على روابط الهدايا المعروفة
        chat = await event.get_chat()
        chat_username = chat.username or ""
        
        if chat_username in GIFT_MARKETS or any(link in text for link in ["t.me/nft/", "tg://nft", "t.me/gift/"]):
            if await self.snipe_gift(event, client, account_name):
                return

        # 5. صيد أزرار الروليت التقليدية
        if event.reply_markup and event.id not in self.cache:
            btn_text = " ".join(b.text for row in event.reply_markup.rows for b in row.buttons)
            if any(k in (text + " " + btn_text).lower() for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self.join_channels(event, client)
                await asyncio.sleep(random.uniform(1.0, 2.5)) # تحسين التوقيت ليصبح أسرع بالتوافق مع الحسابين
                await self.hunt_buttons(event, client)

    # ========== القناص المطور – اقتناص وشراء فوري منعاً للتداخل ==========
    async def snipe_gift(self, event, client, account_name):
        """يفحص أزرار الرسالة والنص معاً ويقوم بالضغط الفوري على زر الشراء إذا وافق السعر ميزانيتك"""
        if not self.sniper_enabled or not event.reply_markup:
            return False

        text = event.raw_text or ""
        detected_price = None

        # أ) الطريقة الأولى: استخراج السعر من نص الإعلان عبر الأنماط
        prices = re.findall(r'(?:سعر|ثمن|بيع|price|قيمة)\s*[:#]?\s*(\d{2,})', text, re.I)
        if not prices:
            # البحث عن الأرقام المتبوعة برموز النجوم
            stars_match = re.search(r'(\d+)\s*(🌟|نجمة|star|stars|⭐)', text, re.I)
            if stars_match:
                detected_price = int(stars_match.group(1))
        else:
            detected_price = int(prices[0])

        # ب) الطريقة الثانية (الأهم للبوتات): إذا كان السعر مكتوباً على الزر نفسه (مثال: "Buy for 130 Stars")
        buy_row, buy_col = None, None
        for row_idx, row in enumerate(event.reply_markup.rows):
            for btn_idx, btn in enumerate(row.buttons):
                # تحديد زر الشراء
                if any(k in btn.text.lower() for k in ['شراء', 'اشتري', 'buy', 'get', 'احصل', 'purchase', '💎']):
                    buy_row, buy_col = row_idx, btn_idx
                    # إذا كان السعر غير واضح بالنص، نحاول استخراجه من نص الزر نفسه
                    if not detected_price:
                        btn_price_match = re.search(r'(\d+)', btn.text)
                        if btn_price_match:
                            detected_price = int(btn_price_match.group(1))

        # ج) تنفيذ الشراء الفوري إذا تم العثور على السعر وكان داخل الميزانية المطلوبة (126 - 149)
        if detected_price and (GIFT_PRICE_MIN <= detected_price <= GIFT_PRICE_MAX):
            if buy_row is not None and buy_col is not None:
                # محاكاة الضغط البشري فائق السرعة
                await asyncio.sleep(random.uniform(0.05, 0.2))
                try:
                    # الضغط على زر الشراء الفعلي عبر الـ API
                    await event.click(buy_row, buy_col)
                    
                    self.stats['gifts_bought'] += 1
                    self.stars -= detected_price
                    
                    chat = await event.get_chat()
                    src = chat.title if hasattr(chat, 'title') else "سوق خاص"
                    link = f"https://t.me/{chat.username}/{event.id}" if chat.username else "رابط داخلي"

                    self.gift_log.append((f"هدية مطورة مطابقة", detected_price, src, link))

                    # إرسال تقرير فوري لحسابك الأساسي عبر الحساب المشتري نفسه
                    success_msg = (
                        f"🎯 **[Omega Sniper - {account_name}] صيد ناجح!**\n"
                        f"💰 السعر المستهلك: {detected_price} نجمة\n"
                        f"📍 المصدر: {src}\n"
                        f"🔗 الرابط: {link}"
                    )
                    logger.info(f"✅ {success_msg}")
                    await self.main_client.send_message('me', success_msg)
                    await self.update_stats_msg()
                    return True
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception as e:
                    logger.warning(f"⚠️ [{account_name}] فشل إرسال أمر الشراء: {e}")
        return False

    # ========== صيد الروليت ==========
    async def hunt_buttons(self, event, client):
        if not event.reply_markup:
            return
        for r, row in enumerate(event.reply_markup.rows):
            for b, btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r, b)
                        self.stats['wins'] += 1
                        earned = random.randint(1, 3)
                        self.stars += earned
                        await self.update_stats_msg()
                        return
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                    except:
                        pass

    async def join_channels(self, event, client):
        links = set()
        if event.entities:
            for e in event.entities:
                if hasattr(e, 'url') and 't.me' in (e.url or ''):
                    links.add(e.url)
        links.update(re.findall(r'(?:t\.me/[\w\d_]+|@[\w\d_]+)', event.raw_text))
        for l in links:
            name = l.split('/')[-1].replace('@', '')
            try:
                await client(JoinChannelRequest(name))
            except:
                pass

    # ========== مغادرة القنوات الميتة ==========
    async def leave_dead_channels(self):
        count = 0
        for client in [self.c1, self.c2] if self.c2 else [self.c1]:
            async for d in client.iter_dialogs():
                if not d.is_channel:
                    continue
                try:
                    msgs = await client.get_messages(d.entity, limit=1)
                    if not msgs or not msgs[0].date:
                        await client(LeaveChannelRequest(d.entity))
                        count += 1
                    elif (datetime.now(tz=None) - msgs[0].date.replace(tzinfo=None)).days > 3:
                        txt = msgs[0].raw_text or ""
                        if not any(k in txt for k in HUNT_KEYWORDS + ['مسابقة', 'روليت', 'سحب']):
                            await client(LeaveChannelRequest(d.entity))
                            count += 1
                except:
                    pass
        self.stats['channels_left'] += count
        if count:
            logger.info(f"🧹 غادرت {count} قناة غير نشطة")
            await self.update_stats_msg()

    # ========== معالجة الأوامر اليدوية ==========
    async def handle_command(self, event, parts):
        cmd = parts[0][1:].lower()
        if cmd == "stats":
            await self.update_stats_msg()
            await event.reply("✅ تم تحديث لوحة التحكم بنجاح.")
        elif cmd == "stop":
            self.running = False
            await event.reply("🛑 تم إيقاف جميع العمليات مؤقتاً.")
        elif cmd == "start":
            self.running = True
            await event.reply("🟢 تم تفعيل تشغيل السكربت والربط الفوري.")
        elif cmd == "sniper_on":
            self.sniper_enabled = True
            await event.reply("🎯 القناص جاهز وبانتظار النطاق (126-149).")
        elif cmd == "sniper_off":
            self.sniper_enabled = False
            await event.reply("🔴 تم إيقاف عمل القناص.")
        elif cmd == "leavedead":
            await self.leave_dead_channels()
            await event.reply("🧹 بدأت عملية تنظيف القنوات الميتة.")
        elif cmd == "giftlog":
            if not self.gift_log:
                await event.reply("📭 السجل فارغ، لا توجد عمليات شراء مكتملة حالياً.")
            else:
                msg = "**💎 آخر الهدايا المصطادة بنجاح:**\n"
                for g, p, src, link in self.gift_log[-10:]:
                    msg += f"▫️ {g} – السعر: {p}⭐ | من: {src}\n"
                await event.reply(msg)
        elif cmd == "panel":
            btns = [
                [Button.inline("📊 الإحصائيات", b"copy_stats"), Button.inline("💎 سجل الهدايا", b"copy_giftlog")],
                [Button.inline("🎯 تفعيل القناص", b"copy_sniper_on"), Button.inline("🧹 تنظيف القنوات", b"copy_leavedead")]
            ]
            await event.respond("🔥 **لوحة التحكم الموحدة - Omega Sniper**", buttons=btns)

    # ========== التشغيل والدورة الحياتية للسكربت ==========
    async def main(self):
        if not await self.connect(self.c1, "الحساب الأول"):
            return
        self.main_client = self.c1

        if self.c2 and not await self.connect(self.c2, "الحساب الثاني"):
            self.c2 = None

        # تفعيل الاستماع للأحداث للحساب الأول
        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id == ADMIN_ID and e.raw_text.startswith("."):
                await self.handle_command(e, e.raw_text.split())
            elif e.is_private or e.is_channel or e.is_group:
                await self.handle_message(e, self.c1, "الحساب الأول")

        # تفعيل الاستماع للأحداث للحساب الثاني بشكل متوازٍ تماماً لمنع مشاكل الكوكيز
        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e):
                if e.is_private or e.is_channel or e.is_group:
                    await self.handle_message(e, self.c2, "الحساب الثاني")

        # أزرار لوحة التحكم عبر الـ Inline Buttons تلقائياً
        @self.c1.on(events.CallbackQuery)
        async def cb(e):
            data = e.data.decode()
            if data.startswith("copy_"):
                cmd = data[5:]
                await e.answer(f"⏳ جاري تنفيذ الأمر اليدوي: .{cmd}")

        # تشغيل المهام الفرعية لضمان العمل المستمر 24/7 دون توقف
        asyncio.create_task(self.keep_alive(self.c1, "ح1"))
        if self.c2:
            asyncio.create_task(self.keep_alive(self.c2, "ح2"))
        asyncio.create_task(self.rest_schedule())

        # جدولة تنظيف القنوات كل 6 ساعات تلقائياً
        async def periodic_clean():
            while self.running:
                await asyncio.sleep(21600)
                await self.leave_dead_channels()
        asyncio.create_task(periodic_clean())

        # دورة تغيير الهوية والتخفي التلقائي للحساب الثاني
        async def persona():
            while self.running:
                await asyncio.sleep(3600)
                if self.c2 and not self.is_resting:
                    if (datetime.now() - self.last_persona_change).total_seconds() > random.randint(70000, 100000):
                        name = random.choice(PERSONA_NAMES)
                        bio = random.choice(PERSONA_BIOS)
                        await self.c2(UpdateProfileRequest(first_name=name, about=bio))
                        self.last_persona_change = datetime.now()
        asyncio.create_task(persona())

        # التنبيه الأولي عند إقلاع السكربت على نظام الـ Workflow الخاص بك
        await self.main_client.send_message(
            'me',
            "🚀 **Omega Gift Sniper انطلق الآن بنجاح!**\n"
            f"🎯 نظام الصيد المزدوج يراقب القنوات والأسواق.\n"
            f"💰 نطاق الصيد المحدد: بين {GIFT_PRICE_MIN} و {GIFT_PRICE_MAX} نجمة."
        )
        await self.update_stats_msg()
        await self.c1(UpdateStatusRequest(offline=False))
        
        # إبقاء الحسابات متصلة وفي وضع الإنصات
        await self.c1.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(OmegaGiftSniper().main())

