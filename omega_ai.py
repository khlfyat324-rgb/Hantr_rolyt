import os, sys, asyncio, random, re, time, json, logging, base64, io, sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from telethon import TelegramClient, events, functions, types, errors, utils
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.errors import (
    FloodWaitError, UsernameOccupiedError, PeerFloodError, UserBannedInChannelError,
    AuthKeyDuplicatedError, RPCError
)
from openai import AsyncOpenAI   # سنستخدمه لاستدعاء DeepSeek عبر OpenAI-compatible API

# ==========================  تهيئة السجلات  ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_ai.log'), logging.StreamHandler()]
)
logger = logging.getLogger("OmegaAI")

# ==========================  الإعدادات العامة (يمكن تغييرها) ==========================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"                # نموذج DeepSeek
AI_ENABLED = True if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "sk-..." else False  # يفعل إذا توفر مفتاح

# مفاتيح تيليجرام (من GitHub Secrets)
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "").strip()
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# الكلمات السوداء للمسابقات الخاسرة (تجنب أى رسالة تحتويها)
BLACKLIST_CONTEST_WORDS = [
    "أكثر نجوم", "من يضع", "تصويت بنجوم", "النجوم الأعلى", "اللي يحط نجوم",
    "giveaway stars", "star rain", "مزاد نجوم", "نجوم على هذه الرسالة"
]

# كلمات المسابقات الآمنة التي نشارك فيها (أول شخص يكتب شيئًا)
SAFE_CONTEST_REGEX = r'(?:أول\s*(?:شخص|واحد|من)\s*(?:ي|يلي)?\s*(?:كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]|[({].*?[)}])\s*(?:\n|$)'

# كلمات عامة للصيد (الروليتات والهدايا)
HUNT_KEYWORDS = [
    "مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "نجوم", "هدية", "تعزيز",
    "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر", "مشاركة (", "المشاركة"
]

# أسماء بنات وغريبة (للهوية المتغيرة)
PERSONA_NAMES = [
    "لارا", "ملاك", "ضائعة", "ليل", "غريبة", "سما", "روح", "فراشة", "سارا", "نور",
    "ظل", "حنين", "لا تسأل", "ماريا", "جانيت", "حائرة", "بنت القمر", "عطر الليل",
    "همسة", "مجهولة", "لطيفة", "غيمة", "ريناد", "تالة", "ليان"
]

# نبذات عشوائية
BIO_TEMPLATES = [
    "ضائعة في عالمي 🌸", "لا تبحث عني فأنا سر 😴", "أحب الصمت والمطر ☔",
    "البساطة عنواني ✨", "انثى من زمن آخر🕊️", "القمر صديقي الوحيد 🌙",
    "لا تعليق 🖤", "مزاجي قهوة وكتاب 📖", "لستُ كما تظن 💫"
]

# الهدف الأدنى لبدء المتاجرة بالهدايا المطورة
MIN_STARS_FOR_SNIPER = 150
# مجلد صور البروفايل (اختياري)
PROFILE_PICS_DIR = "profile_pics"

# ==========================  قاعدة بيانات بسيطة للأسعار  ==========================
PRICE_DB_FILE = "gift_prices.json"

# ==========================  هيكل الذكاء الاصطناعي ==========================
class DeepSeekBrain:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = DEEPSEEK_MODEL

    async def analyse(self, message_text: str, context: dict = None) -> dict:
        """
        يرسل الرسالة إلى DeepSeek ويطلب قرارًا JSON.
        الحقول المتوقعة:
        {
            "action": "ignore" | "hunt" | "safe_contest" | "dangerous_contest" | "reply" | "contact_winner",
            "reply_text": "..." (إن طلب رد),
            "extracted_username": "..." (إن طلب مراسلة بعد فوز),
            "custom_message": "..." (إن احتاج رسالة مخصصة)
        }
        """
        system_prompt = """
        أنت مساعد لنظام صائد هدايا تيليجرام. تعمل كفتاة عمرها 18 سنة. 
        قم بتحليل الرسالة وحدد الإجراء المناسب. ردودك يجب أن تكون قصيرة جدًا (أقل من 10 كلمات في الرد الآلي).
        القواعد:
        - إذا كانت الرسالة تحتوي على أزرار روليت أو سحب أو مشاركة، اكتب action = "hunt".
        - إذا كانت الرسالة تطلب من المستخدم كتابة تعليق معين للفوز (مثل 'أول شخص يكتب تم')، فهي مسابقة آمنة، اكتب action = "safe_contest" مع reply_text = النص المطلوب كتابته (مثلا 'تم').
        - إذا كانت الرسالة تطلب وضع نجوم أو تصويت بنجوم أو فيها 'أكثر نجوم'، فهي مسابقة خطيرة، اكتب action = "dangerous_contest".
        - إذا كانت الرسالة من شخص يطلب رؤية صور أو يقول 'أرسلي صدرك' أو ما شابه، اكتب action = "reply" مع reply_text = "أرسل نجوم الأول 💫" أو رفض لطيف.
        - إذا كانت الرسالة تخبرك أنك فزت وتطلب منك مراسلة شخص معين (يوزر)، اكتب action = "contact_winner" و extracted_username = اسم المستخدم المطلوب، مع custom_message = 'أنا الفائزة...'.
        - إذا كانت محادثة عادية، اختر "reply" مع رد قصير مناسب (مثل 'هلا'، 'كيفك'، 'يسلمو').
        - تجنب الردود الطويلة. كوني فتاة مراهقة بسيطة.
        - إذا كانت الرسالة غير واضحة أو لا تحتاج رد، اكتب action = "ignore".
        رد فقط بصيغة JSON صالحة، لا تضع أي نص إضافي.
        """
        prompt = f"النص:\n{message_text}"
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            # استخراج JSON
            return json.loads(content)
        except Exception as e:
            logger.error(f"DeepSeek Error: {e}")
            return {"action": "ignore"}

# ==========================  المدير الرئيسي (Omega Collector) ==========================
class OmegaAICollector:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.brain = DeepSeekBrain(DEEPSEEK_API_KEY) if AI_ENABLED else None
        self.running = True
        self.stars_balance = 0               # تقديري
        self.sniper_enabled = False
        self.persona_activated = False
        self.last_persona_change = datetime.min
        self.stats = {"wins": 0, "stars_earned": 0, "gifts_bought": 0}
        self.cache = set()
        self.price_db = self._load_price_db()

        # مفاتيح إضافية
        self.trust_mode = True
        self.speed_mode = "auto"
        self.active_commands = {}

    def _load_price_db(self):
        if os.path.exists(PRICE_DB_FILE):
            with open(PRICE_DB_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_price_db(self):
        with open(PRICE_DB_FILE, 'w') as f:
            json.dump(self.price_db, f, indent=2)

    # ==========================  أوامر التحكم (مختصرة لأهم الأوامر) ==========================
    async def execute_command(self, event, cmd_parts):
        cmd = cmd_parts[0][1:].lower()
        args = cmd_parts[1:]
        client2 = self.c2 or self.c1
        try:
            if cmd == "stop":
                self.running = False
                await event.reply("🛑 تم إيقاف المحرك")
            elif cmd == "start":
                self.running = True
                await event.reply("✅ تم تشغيل المحرك")
            elif cmd == "status":
                upt = str(timedelta(seconds=int(time.time() - self.stats.get("start_time", time.time()))))
                await event.reply(f"⚙️ الحالة: {'يعمل' if self.running else 'متوقف'}\n"
                                  f"🏆 صيد: {self.stats['wins']}\n"
                                  f"⭐ نجوم: {self.stars_balance}\n"
                                  f"🎁 مشترى: {self.stats['gifts_bought']}")
            elif cmd == "acc2_phone":
                me = await client2.get_me()
                await event.reply(f"📱 {me.phone or 'غير معروف'}")
            elif cmd == "setname" and args:
                await client2(functions.account.UpdateProfileRequest(first_name=" ".join(args)))
                await event.reply("✅ تم")
            elif cmd == "help":
                await event.reply("أوامر: .stop .start .status .acc2_phone .setname .sniper_on .sniper_off")
            elif cmd == "sniper_on":
                self.sniper_enabled = True
                await event.reply("🎯 مفعل")
            elif cmd == "sniper_off":
                self.sniper_enabled = False
                await event.reply("🎯 معطل")
            # ... إلخ (باقي 100 أمر يمكن إضافتها بنفس النمط)
            else:
                await event.reply("أمر غير معروف")
        except Exception as e:
            await event.reply(f"خطأ: {e}")

    # ==========================  الصيد الذكي ==========================
    async def process_message(self, event, client, is_worker=True):
        if not self.running:
            return
        text = event.raw_text or ""
        if not text and not event.reply_markup:
            return

        # تحليل الرسالة عبر AI (إذا متوفر) وإلا نستخدم كلمات مفتاحية
        if self.brain:
            decision = await self.brain.analyse(text)
            action = decision.get("action", "ignore")
        else:
            # وضع احتياطي بدون AI
            if any(w in text for w in BLACKLIST_CONTEST_WORDS):
                action = "dangerous_contest"
            elif re.search(SAFE_CONTEST_REGEX, text, re.IGNORECASE):
                action = "safe_contest"
                contest_match = re.search(r'[({\[].*?[)}\]]', text)
                reply_text = contest_match.group(0).strip('(){}[]') if contest_match else "تم"
                decision = {"reply_text": reply_text}
            elif any(k in text for k in HUNT_KEYWORDS):
                action = "hunt"
            else:
                action = "reply" if event.is_private else "ignore"

        # تنفيذ القرار
        if action == "hunt":
            await self._execute_hunt(event, client)
        elif action == "safe_contest":
            # اكتب الرد المطلوب (مثلاً "تم") بسرعة
            reply_text = decision.get("reply_text", "تم")
            try:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await event.reply(reply_text)
                logger.info(f"✏️ اشترك في مسابقة آمنة: {reply_text}")
            except: pass
        elif action == "dangerous_contest":
            logger.info(f"🚫 تجنب مسابقة خطيرة")
        elif action == "reply" and event.is_private:
            reply_text = decision.get("reply_text", "هاي")
            await asyncio.sleep(random.uniform(1, 3))
            await self._safe_send(event.reply, reply_text[:50])  # لا تزيد عن 50 حرف
        elif action == "contact_winner":
            username = decision.get("extracted_username", "")
            if username:
                custom_msg = decision.get("custom_message", "أنا الفائزة")
                await self._safe_send(client.send_message, username, custom_msg)
                logger.info(f"✉️ تمت مراسلة {username} بعد الفوز")

        # مسابقات آمنة قد تحتوي أيضًا على أزرار صيد (نفذ الصيد بعد الرد)
        if action == "safe_contest" and event.reply_markup:
            await self._execute_hunt(event, client)

    async def _execute_hunt(self, event, client):
        """صيد الروليت والهدايا"""
        if event.id in self.cache:
            return
        # حل كابتشا
        if await self._solve_captchas(event):
            self.cache.add(event.id)
            return
        if not event.reply_markup:
            return
        # انضمام تلقائي للقنوات
        await self._auto_join(event, client)
        self.cache.add(event.id)
        # تحديد سرعة النقر بناءً على محتوى الرسالة
        urgent = bool(re.search(r'انته|سرعة|فقط|⏳', event.raw_text))
        delay = random.uniform(1, 2.5) if self.speed_mode == "extreme" else random.uniform(5, 9) if urgent else random.uniform(10, 16)
        await asyncio.sleep(delay)
        for row in event.reply_markup.rows:
            for btn in row.buttons:
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(row.row_index, btn.column_index)
                        self.stats["wins"] += 1
                        self.stars_balance += random.randint(1, 5)
                        return
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                    except: pass

    async def _solve_captchas(self, event):
        try:
            text = event.raw_text
            if not event.reply_markup: return False
            # رياضيات
            m = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', text)
            if m:
                res = str(eval(f"{m.group(1)}{m.group(2)}{m.group(3)}"))
                for r, row in enumerate(event.reply_markup.rows):
                    for b, btn in enumerate(row.buttons):
                        if btn.text.strip() == res:
                            await event.click(r, b)
                            return True
            # إيموجي
            em = re.search(r'\((.*?)\)', text)
            if em:
                target = em.group(1).strip()
                for r, row in enumerate(event.reply_markup.rows):
                    for b, btn in enumerate(row.buttons):
                        if target in btn.text:
                            await event.click(r, b)
                            return True
        except: pass
        return False

    async def _auto_join(self, event, client):
        links = set()
        if event.entities:
            for ent in event.entities:
                if isinstance(ent, types.MessageEntityTextUrl) and 't.me' in (ent.url or ''):
                    links.add(ent.url)
        found = re.findall(r'(?:t\.me/[\w\d_]+|@[\w\d_]+)', event.raw_text)
        links.update(found)
        for link in links:
            name = link.split('/')[-1].replace('@', '')
            try: await client(functions.channels.JoinChannelRequest(name))
            except: pass

    async def _safe_send(self, coro, *args, **kwargs):
        try: await coro(*args, **kwargs)
        except FloodWaitError as e: await asyncio.sleep(e.seconds+1); await coro(*args, **kwargs)
        except: pass

    # ==========================  تغيير الهوية (بنت 18) ==========================
    async def persona_loop(self):
        while self.running:
            await asyncio.sleep(3600)  # كل ساعة
            if self.stars_balance >= MIN_STARS_FOR_SNIPER and not self.persona_activated:
                self.persona_activated = True
                self.sniper_enabled = True
                logger.info("🌟 تم تفعيل الشخصية الأنثوية والمتجر")
            if self.persona_activated:
                await self._change_persona()
            elif random.random() < 0.1:  # قبل 150 نجمة نغير أحيانا بشكل عشوائي
                await self._change_persona()

    async def _change_persona(self):
        if datetime.now() - self.last_persona_change < timedelta(hours=random.randint(20, 28)):
            return
        client = self.c2 or self.c1
        try:
            name = random.choice(PERSONA_NAMES)
            await client(functions.account.UpdateProfileRequest(first_name=name))
            bio = random.choice(BIO_TEMPLATES)
            await client(functions.account.UpdateProfileRequest(about=bio))
            # تغيير الصورة إذا وجد مجلد
            if os.path.isdir(PROFILE_PICS_DIR):
                pics = [f for f in os.listdir(PROFILE_PICS_DIR) if f.lower().endswith(('.jpg','.png'))]
                if pics:
                    pic_path = os.path.join(PROFILE_PICS_DIR, random.choice(pics))
                    uploaded = await client.upload_file(pic_path)
                    await client(functions.photos.UploadProfilePhotoRequest(file=uploaded))
                    # حذف الصور القديمة (اختياري)
            self.last_persona_change = datetime.now()
            logger.info(f"🔄 تحولت إلى {name}")
        except Exception as e:
            logger.warning(f"فشل تغيير الهوية: {e}")

    # ==========================  متجر الهدايا المطورة (Sniper) ==========================
    async def sniper_loop(self):
        """مراقبة بوت الهدايا بشكل دوري"""
        logger.info("🎯 بدء مراقبة الهدايا...")
        while self.running:
            if not self.sniper_enabled:
                await asyncio.sleep(10)
                continue
            # محاكاة جلب رسائل من @CollectibleBot (يحتاج لأن يكون مشتركًا بالفعل)
            # سنستمع للرسائل القادمة عبر الأحداث
            await asyncio.sleep(2)  # فقط لمنع الحلقة المفرغة، الأحداث الفعلية تُضاف بالأسفل

    async def monitor_collectible_bot(self, event):
        """عند وصول رسالة من بوت الهدايا"""
        if not self.sniper_enabled: return
        text = event.raw_text or ""
        # تحليل السعر والهدية (بسيط)
        price_match = re.search(r'سعر\s*[:#]?\s*(\d+)', text)
        if not price_match: return
        price = int(price_match.group(1))
        if price < 20 or price > self.stars_balance * 0.6: return
        # البحث عن اسم الهدية
        gift_name = "هدية"
        m = re.search(r'هدية\s+["”“]([^"”“]+)["”“]', text)
        if m: gift_name = m.group(1)
        # سجل السعر
        self.price_db[gift_name] = price
        self._save_price_db()
        # شراء إذا كان السعر أقل من المتوسط (تبسيط)
        if price < self.price_db.get(gift_name, 99999):
            logger.info(f"🔥 شراء {gift_name} بـ {price} نجمة")
            # محاولة النقر على زر الشراء
            if event.reply_markup:
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if 'شراء' in btn.text or 'buy' in btn.text.lower():
                            try:
                                await event.click(row.row_index, btn.column_index)
                                self.stats['gifts_bought'] += 1
                                self.stars_balance -= price
                            except: pass

    # ==========================  المحافظة على الاتصال ==========================
    async def keep_alive(self, client, name="client"):
        while self.running:
            try:
                if not client.is_connected():
                    await client.connect()
                    logger.info(f"🔌 {name} متصل")
                await client(functions.PingRequest(ping_id=random.randint(0, 2**31)))
            except Exception as e:
                logger.warning(f"⚠️ {name} انقطع: {e}")
            await asyncio.sleep(300)

    # ==========================  بدء التشغيل ==========================
    async def main(self):
        self.stats["start_time"] = time.time()
        # اتصال
        try:
            await self.c1.connect()
            if not await self.c1.is_user_authorized():
                logger.critical("Session 1 invalid")
                return
            logger.info("✅ الحساب 1 متصل")
        except AuthKeyDuplicatedError:
            logger.critical("جلسة 1 مكررة - توقف")
            return

        if self.c2:
            try:
                await self.c2.connect()
                if not await self.c2.is_user_authorized():
                    logger.warning("الحساب 2 غير صالح")
                    self.c2 = None
                else:
                    logger.info("✅ الحساب 2 متصل")
            except AuthKeyDuplicatedError:
                logger.critical("جلسة 2 مكررة")
                self.c2 = None

        # تعيين معالجات الأحداث
        @self.c1.on(events.NewMessage)
        async def admin_listener(event):
            if event.sender_id == ADMIN_ID and event.raw_text.startswith("."):
                await self.execute_command(event, event.raw_text.split())
            elif event.is_private:
                await self.process_message(event, self.c1, is_worker=False)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def worker_listener(event):
                await self.process_message(event, self.c2, is_worker=True)

            # مراقبة بوت الهدايا
            @self.c2.on(events.NewMessage(from_users=COLLECTIBLE_BOT))
            async def gift_handler(event):
                await self.monitor_collectible_bot(event)

        # مهام خلفية
        asyncio.create_task(self.keep_alive(self.c1, "Admin"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2, "Worker"))
        asyncio.create_task(self.persona_loop())
        logger.info("🚀 Omega AI Collector بدأ العمل")
        await self.c1.run_until_disconnected()

# ==========================  المدخل ==========================
if __name__ == "__main__":
    try:
        bot = OmegaAICollector()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        logger.info("إيقاف")
