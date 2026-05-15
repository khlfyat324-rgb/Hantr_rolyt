#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
فاطمة الزهراء – الذكاء الاصطناعي البشري (FINAL ULTIMATE)
Ollama LLaMA3 | شخصية بنت 18 من المغرب | ذاكرة | راحة | صيد + شراء
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, asyncio, random, re, json, logging, time, pickle
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ReadHistoryRequest, DeleteHistoryRequest
from telethon.errors import AuthKeyDuplicatedError, FloodWaitError
import ollama

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FatimaFinal")

# ---------- الإعدادات ----------
API_ID_1 = int(os.environ["API_ID_1"]); API_HASH_1 = os.environ["API_HASH_1"]; SESSION_1 = os.environ["SESSION_1"]
API_ID_2 = int(os.environ.get("API_ID_2", 0)); API_HASH_2 = os.environ.get("API_HASH_2", ""); SESSION_2 = os.environ.get("SESSION_2", "")
ADMIN_ID = int(os.environ["ADMIN_ID"])
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")

HUNT_KEYWORDS = ["مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "هدية", "نجوم", "تعزيز",
                 "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"]
DANGER_WORDS = ["أكثر نجوم", "من يضع", "تصويت بنجوم", "اكثر شخص يحط", "يحط يربح", "مزاد نجوم"]
SAFE_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'
PERSONA_NAMES = ["فاطمة الزهراء", "لارا", "ملاك", "ليل", "سما", "روح", "فراشة", "نور"]
PERSONA_BIOS = ["مغربية 🇲🇦 | 18 سنة | لاعب كرة ⚽", "بنت بسيطة من المغرب", "مزاجي كرة وسهر 🌙"]

# ملف الذاكرة
MEMORY_FILE = "fatima_memory.pkl"
# وقت الراحة: 20 دقيقة بعد كل 3 ساعات عمل
REST_INTERVAL_HOURS = 3
REST_DURATION_MINUTES = 20

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
        self.conversations = {}   # ذاكرة المحادثات: {user_id: [ {role, text}, ... ]}
        self.is_resting = False   # هل نحن في فترة راحة؟

    # ---------- الاتصال ----------
    async def iron_connect(self, client, name):
        try:
            await client.connect()
            if await client.is_user_authorized():
                logger.info(f"✅ {name}")
                return True
        except AuthKeyDuplicatedError:
            logger.critical(f"🔑 {name} جلسة مكررة! أعد توليدها.")
        except Exception as e:
            logger.error(f"❌ {name}: {e}")
        return False

    async def keep_alive(self, client, name):
        while self.running:
            if not self.is_resting:   # أرسل البينغ فقط في وقت العمل
                try:
                    if not client.is_connected():
                        await client.connect()
                    await client(UpdateStatusRequest(offline=False))
                except: pass
            else:
                # في الراحة، نظهر غير متصل
                try:
                    await client(UpdateStatusRequest(offline=True))
                except: pass
            await asyncio.sleep(60)

    # ---------- جدول الراحة ----------
    async def rest_schedule(self):
        while self.running:
            await asyncio.sleep(REST_INTERVAL_HOURS * 3600)  # اعمل 3 ساعات
            self.is_resting = True
            logger.info("😴 بدء فترة الراحة 20 دقيقة...")
            await asyncio.sleep(REST_DURATION_MINUTES * 60)
            self.is_resting = False
            logger.info("☀️ انتهت الراحة، العودة للعمل")

    # ---------- ذاكرة المحادثات ----------
    def get_conversation(self, user_id):
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]

    def add_to_conversation(self, user_id, role, text):
        conv = self.get_conversation(user_id)
        conv.append({"role": role, "text": text})
        if len(conv) > 20:   # نحتفظ بآخر 20 رسالة
            conv.pop(0)

    # ---------- رسالة الإحصائيات الحية ----------
    async def update_stats_msg(self):
        global STATS_MSG_ID
        if not self.main_client: return
        uptime = str(timedelta(seconds=int(time.time()-self.stats['start'])))
        status = "😴 راحة" if self.is_resting else "🟢 نشطة"
        msg = (
            f"📊 **فاطمة الزهراء** ({status})\n"
            f"🕒 {datetime.now().strftime('%H:%M:%S')}\n"
            f"⏱️ {uptime}\n"
            f"🏆 صيد: {self.stats['wins']}\n"
            f"⭐ رصيد: ~{self.stats['stars']}\n"
            f"💎 مشتراة: {self.stats['gifts_bought']}\n"
            f"🎁 محولة: {self.stats['gifts_converted']}\n"
            f"🚪 غادرت: {self.stats['channels_left']}\n"
            f"📨 رسائل: {self.stats['msgs_processed']}\n"
            f"🎯 القناص: {'🟢' if self.sniper_enabled else '🔴'}"
        )
        try:
            if STATS_MSG_ID:
                await self.main_client.edit_message('me', STATS_MSG_ID, msg)
            else:
                sent = await self.main_client.send_message('me', msg)
                STATS_MSG_ID = sent.id
        except Exception as e:
            logger.warning(f"تحديث الإحصائيات: {e}")

    # ---------- تحليل AI مع الذاكرة ----------
    async def analyze(self, text, user_id=None):
        try:
            # بناء الذاكرة
            memory_context = ""
            if user_id:
                conv = self.get_conversation(user_id)
                lines = [f"{'أنتِ' if m['role']=='assistant' else 'المستخدم'}: {m['text']}" for m in conv[-5:]]
                memory_context = "تاريخ المحادثة:\n" + "\n".join(lines) if lines else ""

            system = (
                "أنتِ 'فاطمة الزهراء'، بنت 18 سنة من المغرب، تحبين كرة القدم. "
                "تتحدثين العامية المغربية/الشرقية. ردودك قصيرة جداً (3-10 كلمات). "
                "لا تكشفي أبداً أنك ذكاء اصطناعي. "
                "حللي الرسالة واختاري الإجراء بصيغة JSON: "
                '{"action":"hunt"|"safe_contest"|"dangerous_contest"|"reply"|"ignore", '
                '"reply_text":"..."} '
                "إذا كانت أزرار روليت/سحب → hunt. "
                "إذا 'أول شخص يكتب...' → safe_contest مع الكلمة المطلوبة. "
                "إذا 'اكثر نجوم' أو 'يحط يربح' → dangerous_contest. "
                "إذا محادثة خاصة عادية → reply مع رد طبيعي جداً."
            )
            user_msg = f"الذاكرة:\n{memory_context}\n\nالرسالة الجديدة:\n{text}"
            resp = ollama.chat(model=OLLAMA_MODEL,
                               messages=[{"role":"system","content":system},
                                         {"role":"user","content":user_msg}],
                               format="json", options={"temperature":0.8, "max_tokens":100})
            return json.loads(resp['message']['content'])
        except Exception as e:
            logger.error(f"Ollama: {e}")
            return {"action":"ignore"}

    # ---------- هدايا النجوم الحقيقية ----------
    async def handle_star_gift(self, event, client):
        if isinstance(event.message.action, types.MessageActionStarGift):
            if event.reply_markup:
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if any(k in btn.text for k in ['تحويل','نجمة','convert']):
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_converted'] += 1
                            self.stats['stars'] += random.randint(10,50)
                            await self.update_stats_msg()
                            break
            thanks = random.choice(["يسلمووو ❤️","تسلم يالغالي 🌸","واااي شكراً 💫","الله يسعدك 🌟"])
            await asyncio.sleep(random.uniform(1,3))
            try: await event.reply(thanks)
            except: pass
            return True
        return False

    # ---------- تحويل هدايا عادية ----------
    async def convert_gift(self, event, client):
        if event.reply_markup and any(w in (event.raw_text or "") for w in ['هدية من','أضاف','الهدية']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل','نجمة','convert','stars']):
                        await event.click(row.row_index, btn.column_index)
                        self.stats['gifts_converted'] += 1
                        self.stats['stars'] += random.randint(10,50)
                        await self.update_stats_msg()
                        try: await client(DeleteHistoryRequest(peer=event.chat_id, max_id=0, just_clear=True))
                        except: pass
                        return True
        return False

    # ---------- صيد الهدايا المطورة (القناص) ----------
    async def snipe_gifts(self, event, client):
        if not self.sniper_enabled or not event.reply_markup:
            return False
        text = event.raw_text or ""
        # البحث عن أسعار بين 100-130 (يمكنك تعديل النطاق)
        prices = re.findall(r'(?:سعر|ثمن|بيع|price)\s*[:#]?\s*(\d{2,})', text, re.I)
        for p_str in prices:
            price = int(p_str)
            if 100 <= price <= 130 and self.stats >= price:
                gift_name = "هدية"
                m = re.search(r'(?:هدية|Gift|مقتني)\s*["\']?([\w\s]+)', text, re.I)
                if m: gift_name = m.group(1).strip()
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if any(k in btn.text for k in ['شراء','اشتري','buy','get']):
                            await asyncio.sleep(random.uniform(0.3, 0.8))
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_bought'] += 1
                            self.stars -= price
                            chat = await event.get_chat()
                            src = chat.title if hasattr(chat,'title') else "خاص"
                            # الحصول على رابط الهدية إن أمكن
                            link = f"https://t.me/{chat.username}/{event.id}" if chat.username else ""
                            self.gift_log.append((gift_name, price, src, link))
                            await self.main_client.send_message('me',
                                f"💎 **صيد هدية مطورة!**\n"
                                f"الاسم: {gift_name}\n"
                                f"السعر: {price} نجمة\n"
                                f"المصدر: {src}\n"
                                f"الرابط: {link or 'غير متوفر'}"
                            )
                            await self.update_stats_msg()
                            return True
        return False

    # ---------- معالجة الرسالة الأساسية ----------
    async def process(self, event, client):
        if not self.running: return
        # لا ترد على رسائلنا الصادرة أبداً
        if event.out: return
        # في فترة الراحة، لا نتفاعل مع أي شيء
        if self.is_resting: return

        self.stats['msgs_processed'] += 1
        user_id = event.sender_id

        # 1. هدايا النجوم الحقيقية
        if await self.handle_star_gift(event, client): return

        # 2. تحويل الهدايا العادية
        if await self.convert_gift(event, client): return

        text = event.raw_text or ""
        # إضافة رسالة المستخدم للذاكرة
        self.add_to_conversation(user_id, "user", text)

        # 3. تحليل AI
        decision = await self.analyze(text, user_id)
        action = decision.get("action", "ignore")

        # 4. تنفيذ
        if action == "dangerous_contest": return
        elif action == "safe_contest":
            reply = decision.get("contest_reply", "تم")
            try: await event.reply(reply)
            except: pass
            if event.reply_markup:
                await self.hunt_buttons(event, client)
        elif action == "hunt" or (event.reply_markup and event.id not in self.cache):
            if event.reply_markup and event.id not in self.cache:
                btn_text = "".join(b.text for r in event.reply_markup.rows for b in r.buttons)
                if any(k in (text + btn_text).lower() for k in HUNT_KEYWORDS):
                    self.cache.add(event.id)
                    await self.auto_join(event, client)
                    await asyncio.sleep(random.uniform(2,5))
                    await self.hunt_buttons(event, client)
        elif action == "reply" and event.is_private:
            reply_text = decision.get("reply_text")
            if reply_text:
                # محاكاة بشرية
                await asyncio.sleep(random.uniform(3,10))
                try: await client(ReadHistoryRequest(peer=event.chat_id, max_id=event.id))
                except: pass
                await asyncio.sleep(random.uniform(1,2))
                async with client.action(event.chat_id, 'typing'):
                    await asyncio.sleep(random.uniform(1,2))
                try:
                    await event.reply(reply_text)
                    # أضف ردنا للذاكرة
                    self.add_to_conversation(user_id, "assistant", reply_text)
                except: pass

        # 5. القناص
        await self.snipe_gifts(event, client)

        # تحديث الإحصائيات كل فترة
        if self.stats['msgs_processed'] % 5 == 0:
            await self.update_stats_msg()

    # ---------- الصيد ----------
    async def hunt_buttons(self, event, client):
        if not event.reply_markup: return
        for r,row in enumerate(event.reply_markup.rows):
            for b,btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r,b)
                        self.stats['wins'] += 1
                        self.stats['stars'] += random.randint(1,5)
                        if not self.sniper_enabled and self.stats['stars'] >= 100:
                            self.sniper_enabled = True
                        await self.update_stats_msg()
                        return
                    except FloodWaitError as e: await asyncio.sleep(e.seconds+1)
                    except: pass

    async def auto_join(self, event, client):
        links=set()
        if event.entities:
            for e in event.entities:
                if hasattr(e,'url') and 't.me' in (e.url or ''): links.add(e.url)
        links.update(re.findall(r't\.me/[\w\d_]+|@[\w\d_]+', event.raw_text))
        for l in links:
            name=l.split('/')[-1].replace('@','')
            try: await client(JoinChannelRequest(name))
            except: pass

    # ---------- أوامر ----------
    async def handle_command(self, event, parts, client):
        cmd = parts[0][1:].lower()
        if cmd=="stats": await self.update_stats_msg(); await event.reply("✅ تم تحديث الإحصائيات")
        elif cmd=="stop": self.running=False; await event.reply("🛑 توقف")
        elif cmd=="start": self.running=True; await event.reply("✅ تشغيل")
        elif cmd=="sniper_on": self.sniper_enabled=True; await event.reply("🎯")
        elif cmd=="sniper_off": self.sniper_enabled=False; await event.reply("🎯")
        elif cmd=="leavedead":
            count=0
            for cl in [self.c1, self.c2] if self.c2 else [self.c1]:
                async for d in cl.iter_dialogs():
                    if not d.is_channel: continue
                    try:
                        m = await cl.get_messages(d.entity, limit=1)
                        if not m or not m[0].date: await cl(LeaveChannelRequest(d.entity)); count+=1
                    except: pass
            self.stats['channels_left']+=count
            await event.reply(f"🧹 غادرت {count}")
            await self.update_stats_msg()
        elif cmd=="panel":
            btns = [[Button.inline(".stats", b"stats"), Button.inline(".stop", b"stop")]]
            await event.respond("🔥 **أوامر فاطمة الزهراء**", buttons=btns)
        elif cmd=="rest":   # أمر يدوي لبدء الراحة
            self.is_resting = True
            await event.reply("😴 تم الدخول في الراحة 20 دقيقة")

    # ---------- تشغيل ----------
    async def main(self):
        if not await self.iron_connect(self.c1, "حساب 1"): return
        self.main_client = self.c1
        # تحقق من تفعيل القناص مباشرة إذا الرصيد كافٍ
        if self.stars >= 100: self.sniper_enabled = True

        if self.c2:
            if await self.iron_connect(self.c2, "حساب 2"):
                logger.info("✅ الحساب 2 متصل")
            else:
                self.c2 = None

        # معالجات الأحداث
        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id==ADMIN_ID and e.raw_text.startswith("."):
                await self.handle_command(e, e.raw_text.split(), self.c1)
            else:
                await self.process(e, self.c1)
        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e): await self.process(e, self.c2)

        # مهام الخلفية
        asyncio.create_task(self.keep_alive(self.c1, "ح1"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2, "ح2"))
        asyncio.create_task(self.rest_schedule())

        # تنظيف دوري
        async def periodic():
            while self.running:
                await asyncio.sleep(14400)
                for cl in [self.c1, self.c2] if self.c2 else [self.c1]:
                    await self.leave_dead(cl)
        asyncio.create_task(periodic())

        # شخصية الحساب الثاني
        async def persona():
            while self.running:
                await asyncio.sleep(3600)
                if self.c2 and not self.is_resting:
                    if (datetime.now()-self.last_persona_change).total_seconds() > random.randint(70000,100000):
                        name = random.choice(PERSONA_NAMES)
                        bio = random.choice(PERSONA_BIOS)
                        await self.c2(UpdateProfileRequest(first_name=name, about=bio))
                        self.last_persona_change = datetime.now()
        asyncio.create_task(persona())

        # إرسال قائمة الأوامر الأولية
        await self.main_client.send_message('me', 
            "👋 **فاطمة الزهراء جاهزة**\n"
            "📋 الأوامر: .stats, .stop, .start, .sniper_on, .sniper_off, .leavedead, .panel, .rest"
        )
        await self.update_stats_msg()
        await self.c1(UpdateStatusRequest(offline=False))
        logger.info("🚀 فاطمة الزهراء انطلقت (النسخة البشرية)")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    STATS_MSG_ID = None
    asyncio.run(FatimaBot().main())
