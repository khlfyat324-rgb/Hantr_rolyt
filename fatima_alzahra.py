#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
فاطمة الزهراء – الإصدار الأسطوري النهائي (Fix Final)
نموذج Groq: llama-3.3-70b-versatile | ردود بشرية 100% | انتظار ذكي
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, asyncio, random, re, json, logging, time
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ReadHistoryRequest, DeleteHistoryRequest
from telethon.errors import AuthKeyDuplicatedError, FloodWaitError
from groq import AsyncGroq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FatimaFinal")

# ---------- الإعدادات (أسرار) ----------
API_ID_1 = int(os.environ["API_ID_1"]); API_HASH_1 = os.environ["API_HASH_1"]; SESSION_1 = os.environ["SESSION_1"]
API_ID_2 = int(os.environ.get("API_ID_2", 0)); API_HASH_2 = os.environ.get("API_HASH_2", ""); SESSION_2 = os.environ.get("SESSION_2", "")
ADMIN_ID = int(os.environ["ADMIN_ID"])
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

HUNT_KEYWORDS = ["مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "هدية", "نجوم", "تعزيز",
                 "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"]
DANGER_WORDS = ["أكثر نجوم", "من يضع", "تصويت بنجوم", "اكثر شخص يحط", "يحط يربح", "مزاد نجوم"]
SAFE_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'
PERSONA_NAMES = ["فاطمة الزهراء", "لارا", "ملاك", "ليل", "سما", "روح", "فراشة", "نور"]
PERSONA_BIOS = ["مغربية 🇲🇦 | 18 سنة | لاعبة كرة ⚽", "بنت بسيطة من المغرب", "مزاجي كرة وسهر 🌙"]

STATS_MSG_ID = None

class FatimaBot:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stars = 0
        self.sniper_enabled = False
        self.last_persona_change = datetime.min
        self.cache = set()
        self.gift_log = []
        self.stats = {"wins":0, "stars":0, "gifts_bought":0, "gifts_converted":0,
                      "channels_left":0, "msgs_processed":0, "start":time.time()}
        self.main_client = None
        self.conversations = {}          # {user_id: [msgs]}
        self.pending_timers = {}         # {user_id: asyncio.Task} لتأخير الرد
        self.is_resting = False
        self.ai = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.ai_fail_count = 0
        self.ai_paused_until = None

    # ========== اتصال ==========
    async def connect(self, client, name):
        try:
            await client.connect()
            if await client.is_user_authorized():
                logger.info(f"✅ {name}")
                return True
        except AuthKeyDuplicatedError:
            logger.critical(f"🔑 {name} الجلسة مكررة! لا تفتح الحساب من مكان آخر.")
        except Exception as e:
            logger.error(f"❌ {name}: {e}")
        return False

    async def keep_alive(self, client, name):
        while self.running:
            if not self.is_resting:
                try:
                    if not client.is_connected(): await client.connect()
                    await client(UpdateStatusRequest(offline=False))
                except: pass
            else:
                try: await client(UpdateStatusRequest(offline=True))
                except: pass
            await asyncio.sleep(60)

    async def rest_schedule(self):
        while self.running:
            await asyncio.sleep(3 * 3600)
            self.is_resting = True; logger.info("😴 راحة 20 دقيقة...")
            await asyncio.sleep(20 * 60)
            self.is_resting = False; logger.info("☀️ رجعت للعمل")

    # ========== ذاكرة المحادثات ==========
    def get_conv(self, uid):
        if uid not in self.conversations:
            self.conversations[uid] = []
        return self.conversations[uid]

    def add_conv(self, uid, role, text):
        c = self.get_conv(uid)
        c.append({"role": role, "text": text})
        if len(c) > 20: c.pop(0)

    # ========== إحصائيات حية ==========
    async def update_stats_msg(self):
        global STATS_MSG_ID
        if not self.main_client: return
        uptime = str(timedelta(seconds=int(time.time()-self.stats['start'])))
        status = "😴 راحة" if self.is_resting else "🟢 نشطة"
        msg = (
            f"📊 **فاطمة الزهراء** ({status})\n"
            f"🕒 {datetime.now().strftime('%H:%M:%S')}\n⏱️ {uptime}\n"
            f"🏆 صيد: {self.stats['wins']}\n⭐ رصيد: ~{self.stats['stars']}\n"
            f"💎 مشتراة: {self.stats['gifts_bought']}\n🎁 محولة: {self.stats['gifts_converted']}\n"
            f"🚪 غادرت: {self.stats['channels_left']}\n📨 رسائل: {self.stats['msgs_processed']}\n"
            f"🎯 القناص: {'🟢' if self.sniper_enabled else '🔴'}"
        )
        try:
            if STATS_MSG_ID: await self.main_client.edit_message('me', STATS_MSG_ID, msg)
            else:
                sent = await self.main_client.send_message('me', msg)
                STATS_MSG_ID = sent.id
        except: pass

    # ========== معالج القنوات (سريع) ==========
    async def handle_public(self, event, client):
        text = event.raw_text or ""
        # تحويل الهدايا
        if event.reply_markup and any(w in text for w in ['هدية من','أضاف','الهدية']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل','نجمة','convert','stars']):
                        await event.click(row.row_index, btn.column_index)
                        self.stats['gifts_converted'] += 1
                        self.stats['stars'] += random.randint(10,50)
                        await self.update_stats_msg()
                        try: await client(DeleteHistoryRequest(peer=event.chat_id, max_id=0, just_clear=True))
                        except: pass
                        return
        if any(w in text for w in DANGER_WORDS): return
        safe = re.search(SAFE_REGEX, text, re.I)
        if safe:
            reply = re.search(r'[({\[].*?[)}\]]', text)
            reply_text = reply.group(0).strip('(){}[]') if reply else "تم"
            try: await event.reply(reply_text)
            except: pass
            if event.reply_markup: await self.hunt(event, client)
            return
        if event.reply_markup and event.id not in self.cache:
            btn_text = "".join(b.text for r in event.reply_markup.rows for b in r.buttons)
            if any(k in (text + " " + btn_text).lower() for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self.join(event, client)
                await asyncio.sleep(random.uniform(1.5, 4))
                await self.hunt(event, client)
                return
        await self.snipe(event, client)

    # ========== الرسائل الخاصة (مع انتظار ذكي) ==========
    async def handle_private(self, event, client):
        if event.out: return
        if event.sender and event.sender.bot: return  # تجاهل البوتات

        uid = event.sender_id

        # هدايا النجوم
        if isinstance(event.message.action, types.MessageActionStarGift):
            if event.reply_markup:
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if any(k in btn.text for k in ['تحويل','نجمة','convert']):
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_converted'] += 1
                            self.stats['stars'] += random.randint(10,50)
                            await self.update_stats_msg()
            thanks = random.choice(["يسلمووو ❤️","تسلم خويا 🌸","واااي شكراً 💫"])
            await asyncio.sleep(random.uniform(1,2))
            try: await event.reply(thanks)
            except: pass
            return

        # إضافة الرسالة إلى الذاكرة
        text = event.raw_text or ""
        self.add_conv(uid, "user", text)

        # إلغاء أي مؤقت سابق لهذا المستخدم (سننتظر المزيد من الرسائل)
        if uid in self.pending_timers:
            self.pending_timers[uid].cancel()
            logger.info(f"⏳ إلغاء مؤقت سابق للمستخدم {uid}، في انتظار رسائل إضافية")

        # إنشاء مؤقت جديد للرد بعد فترة صمت (4-7 ثوانٍ)
        async def delayed_reply():
            await asyncio.sleep(random.uniform(4, 7))
            # حان وقت الرد، نأخذ كل الرسائل المتراكمة من هذا المستخدم
            conv = self.get_conv(uid)
            # نعالج فقط الرسائل الجديدة (غير المقروءة بعد) - لكننا سنعالج كل شيء معاً
            # نرسل رد واحد بناءً على مجمل المحادثة
            reply = await self.generate_reply(uid, event)
            if reply:
                await asyncio.sleep(random.uniform(1, 2))
                try: await client(ReadHistoryRequest(peer=event.chat_id, max_id=event.id))
                except: pass
                await asyncio.sleep(random.uniform(0.5, 1.5))
                async with client.action(event.chat_id, 'typing'):
                    await asyncio.sleep(random.uniform(0.8, 2))
                try:
                    await client.send_message(event.chat_id, reply)
                    self.add_conv(uid, "assistant", reply)
                except: pass
            # تنظيف المؤقت
            if uid in self.pending_timers:
                del self.pending_timers[uid]

        task = asyncio.create_task(delayed_reply())
        self.pending_timers[uid] = task

    async def generate_reply(self, uid, event):
        """توليد رد واحد بناءً على المحادثة الكاملة مع هذا المستخدم"""
        # استخدام AI إذا متاح، وإلا ردود محلية
        if self.ai and (not self.ai_paused_until or datetime.now() >= self.ai_paused_until) and self.ai_fail_count < 3:
            try:
                sender = await event.get_sender()
                sender_name = sender.first_name or "خويا"
                conv = self.get_conv(uid)
                # بناء تاريخ المحادثة
                history = "\n".join([f"{'هي' if m['role']=='assistant' else sender_name}: {m['text']}" for m in conv[-10:]])
                system_prompt = (
                    "أنتِ 'فاطمة الزهراء'، بنت من المغرب عمرك 18 سنة. لاعبة كرة، شخصية لطيفة. "
                    "تتحدثين بالعامية المناسبة للشخص (مغربية، مصرية، خليجية...). "
                    "ردودك قصيرة (3-12 كلمة). لا تكررين نفس الكلام. لا تقولين 'غالي' للذكور. "
                    "إذا قال 'مرحبا' ردي 'أهلاً'. إذا قال 'كيفاش' ردي 'لباس الحمد لله'. "
                    "لا تخبرين أحداً أنك ذكاء اصطناعي. ردي ب JSON: {\"reply_text\": \"...\"}"
                )
                prompt = f"اسم المستخدم: {sender_name}\nآخر المحادثة:\n{history}\n\nاكتبي رداً واحداً مناسباً لكل الرسائل السابقة."
                response = await self.ai.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"system","content":system_prompt},
                             {"role":"user","content":prompt}],
                    temperature=0.9, max_tokens=50,
                    response_format={"type":"json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                reply = data.get("reply_text")
                if reply:
                    self.ai_fail_count = 0
                    return reply
            except Exception as e:
                logger.error(f"AI فشل: {e}")
                self.ai_fail_count += 1
                if self.ai_fail_count >= 3:
                    self.ai_paused_until = datetime.now() + timedelta(minutes=5)
        # رد احتياطي
        return self.fallback_reply(uid)

    def fallback_reply(self, uid):
        """رد محلي سريع يعتمد على آخر رسالة فقط"""
        conv = self.get_conv(uid)
        if not conv: return "أهلاً 🌸"
        last_msg = conv[-1]['text'].lower()
        if any(w in last_msg for w in ['مرحبا','سلام','اهلا']):
            return random.choice(["أهلاً وسهلاً 🌸","هلا والله","مراحب"])
        if 'كيفك' in last_msg or 'شخبارك' in last_msg:
            return random.choice(["الحمد لله بخير","تمام شكراً ونتا؟"])
        return random.choice(["🌸","هلا","أهلاً"])

    # ========== الصيد والقناص ==========
    async def hunt(self, event, client):
        if not event.reply_markup: return
        for r,row in enumerate(event.reply_markup.rows):
            for b,btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r,b)
                        self.stats['wins'] += 1
                        self.stats['stars'] += random.randint(1,5)
                        if not self.sniper_enabled and self.stars >= 100:
                            self.sniper_enabled = True
                        await self.update_stats_msg()
                        return
                    except FloodWaitError as e: await asyncio.sleep(e.seconds+1)
                    except: pass

    async def join(self, event, client):
        links = set()
        if event.entities:
            for e in event.entities:
                if hasattr(e,'url') and 't.me' in (e.url or ''): links.add(e.url)
        links.update(re.findall(r't\.me/[\w\d_]+|@[\w\d_]+', event.raw_text))
        for l in links:
            name=l.split('/')[-1].replace('@','')
            try: await client(JoinChannelRequest(name))
            except: pass

    async def snipe(self, event, client):
        if not self.sniper_enabled or not event.reply_markup: return
        text = event.raw_text or ""
        prices = re.findall(r'(?:سعر|ثمن|بيع|price|قيمة)\s*[:#]?\s*(\d{2,})', text, re.I)
        for p_str in prices:
            price = int(p_str)
            if 80 <= price <= 150 and self.stars >= price:
                gift = "هدية"
                m = re.search(r'(?:هدية|Gift|مقتني)\s*["\']?([\w\s]+)', text, re.I)
                if m: gift = m.group(1).strip()
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if any(k in btn.text for k in ['شراء','اشتري','buy','get']):
                            await asyncio.sleep(random.uniform(0.3,0.6))
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_bought'] += 1; self.stars -= price
                            chat = await event.get_chat()
                            src = chat.title if hasattr(chat,'title') else "خاص"
                            link = f"https://t.me/{chat.username}/{event.id}" if chat.username else ""
                            self.gift_log.append((gift, price, src, link))
                            await self.main_client.send_message('me',
                                f"💎 **صيد هدية!**\nالاسم: {gift}\nالسعر: {price}⭐\nالمصدر: {src}\nالرابط: {link}")
                            await self.update_stats_msg()
                            return True
        return False

    # ========== أوامر ==========
    async def handle_command(self, event, parts):
        cmd = parts[0][1:].lower()
        if cmd=="stats": await self.update_stats_msg(); await event.reply("✅ تم")
        elif cmd=="stop": self.running=False; await event.reply("🛑")
        elif cmd=="start": self.running=True; await event.reply("✅")
        elif cmd=="sniper_on": self.sniper_enabled=True; await event.reply("🎯 مفعل")
        elif cmd=="sniper_off": self.sniper_enabled=False; await event.reply("🔴 معطل")
        elif cmd=="leavedead":
            c=0
            for cl in [self.c1, self.c2] if self.c2 else [self.c1]:
                async for d in cl.iter_dialogs():
                    if not d.is_channel: continue
                    try:
                        m = await cl.get_messages(d.entity, limit=1)
                        if not m or not m[0].date: await cl(LeaveChannelRequest(d.entity)); c+=1
                    except: pass
            self.stats['channels_left']+=c; await event.reply(f"🧹 {c}")
            await self.update_stats_msg()
        elif cmd=="panel":
            await event.respond("🔥 أوامر فاطمة", buttons=[Button.inline(".stats",b"stats")])

    # ========== تشغيل ==========
    async def main(self):
        if not await self.connect(self.c1, "ح1"): return
        self.main_client = self.c1
        if self.stars >= 100: self.sniper_enabled = True

        if self.c2 and not await self.connect(self.c2, "ح2"): self.c2 = None

        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id==ADMIN_ID and e.raw_text.startswith("."):
                await self.handle_command(e, e.raw_text.split())
            elif e.is_private:
                await self.handle_private(e, self.c1)
            else:
                if self.running and not self.is_resting:
                    self.stats['msgs_processed'] += 1
                    await self.handle_public(e, self.c1)
                    if self.stats['msgs_processed'] % 5 == 0: await self.update_stats_msg()

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e):
                if e.is_private: await self.handle_private(e, self.c2)
                elif self.running and not self.is_resting: await self.handle_public(e, self.c2)

        asyncio.create_task(self.keep_alive(self.c1,"ح1"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2,"ح2"))
        asyncio.create_task(self.rest_schedule())

        # تنظيف القنوات
        async def periodic():
            while self.running:
                await asyncio.sleep(14400)
                for cl in [self.c1, self.c2] if self.c2 else [self.c1]:
                    c=0
                    async for d in cl.iter_dialogs():
                        if not d.is_channel: continue
                        try:
                            m = await cl.get_messages(d.entity, limit=1)
                            if not m or not m[0].date: await cl(LeaveChannelRequest(d.entity)); c+=1
                        except: pass
                    self.stats['channels_left']+=c
                await self.update_stats_msg()
        asyncio.create_task(periodic())

        # شخصية الحساب الثاني
        async def persona():
            while self.running:
                await asyncio.sleep(3600)
                if self.c2 and not self.is_resting and self.sniper_enabled:
                    if (datetime.now()-self.last_persona_change).total_seconds() > random.randint(70000,100000):
                        name = random.choice(PERSONA_NAMES); bio = random.choice(PERSONA_BIOS)
                        await self.c2(UpdateProfileRequest(first_name=name, about=bio))
                        self.last_persona_change = datetime.now()
        asyncio.create_task(persona())

        await self.main_client.send_message('me', "👋 فاطمة الزهراء جاهزة\n.help للأوامر")
        await self.update_stats_msg()
        await self.c1(UpdateStatusRequest(offline=False))
        logger.info("🚀 فاطمة الأسطورية انطلقت")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(FatimaBot().main())
