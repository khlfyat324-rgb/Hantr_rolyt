#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
فاطمة الزهراء – الإصدار الأسطوري النهائي
حسابان (الثاني يغير اسمه) | Ollama LLaMA3 | ذاكرة وتعلم | صيد + شراء + بيع
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, asyncio, random, re, json, logging, time, pickle
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ReadHistoryRequest, DeleteHistoryRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.errors import AuthKeyDuplicatedError, FloodWaitError
import ollama

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FatimaFinal")

# ---------- المتغيرات البيئية ----------
API_ID_1 = int(os.environ["API_ID_1"]); API_HASH_1 = os.environ["API_HASH_1"]; SESSION_1 = os.environ["SESSION_1"]
API_ID_2 = int(os.environ.get("API_ID_2", 0)); API_HASH_2 = os.environ.get("API_HASH_2", ""); SESSION_2 = os.environ.get("SESSION_2", "")
ADMIN_ID = int(os.environ["ADMIN_ID"])
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")

HUNT_KEYWORDS = ["مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "هدية", "نجوم", "تعزيز",
                 "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"]
DANGER_WORDS = ["أكثر نجوم", "من يضع", "تصويت بنجوم", "اكثر شخص يحط", "يحط يربح", "مزاد نجوم"]
SAFE_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'
PERSONA_NAMES = ["فاطمة الزهراء", "لارا", "ملاك", "ليل", "سما", "روح", "فراشة", "نور"]
PERSONA_BIOS = ["لاعبة كرة ⚽ | 18 سنة", "بنت بسيطة تعشق الكورة", "مزاجي كرة وسهر 🌙"]

STATS_MSG_ID = None

# ---------- ذاكرة التعلم ----------
MEMORY_FILE = "fatima_memory.pkl"
MAX_MEMORY = 200

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
        self.memory = []   # قائمة لتخزين الأمثلة (للتعلم)
        self.load_memory()

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'rb') as f:
                    self.memory = pickle.load(f)[-MAX_MEMORY:]
            except: pass

    def save_memory(self):
        with open(MEMORY_FILE, 'wb') as f:
            pickle.dump(self.memory, f)

    async def iron_connect(self, client, name):
        for _ in range(10):
            try:
                await client.connect()
                if await client.is_user_authorized(): logger.info(f"✅ {name}"); return True
            except AuthKeyDuplicatedError: await client.disconnect(); await asyncio.sleep(60)
            except Exception as e: await asyncio.sleep(15)
        return False

    async def keep_alive(self, client, name):
        while self.running:
            try:
                if not client.is_connected(): await self.iron_connect(client, name)
                await client(UpdateStatusRequest(offline=False))
                await client(functions.PingRequest(ping_id=random.randint(0,2**31)))
            except: pass
            await asyncio.sleep(120)

    # ---------- رسالة إحصائيات حية ----------
    async def update_stats_msg(self):
        global STATS_MSG_ID
        uptime = str(timedelta(seconds=int(time.time()-self.stats['start'])))
        msg = (
            f"📊 **فاطمة الزهراء – حية**\n"
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
        except Exception as e: logger.warning(f"تحديث الإحصائيات: {e}")

    # ---------- تحليل بالذكاء الاصطناعي (Ollama) ----------
    async def analyze(self, text):
        context = "\n".join(self.memory[-5:]) if self.memory else ""
        system = (
            "أنت 'فاطمة الزهراء'، فتاة 18 سنة، تحب الكرة، تتحدثين العامية الشرقية. "
            "لا تكشفي أبداً أنك AI. ردودك قصيرة (3-10 كلمات). "
            "حللي الرسالة واختاري الإجراء بصيغة JSON: "
            '{"action":"hunt"|"safe_contest"|"dangerous_contest"|"reply"|"contact_winner"|"ignore", '
            '"contest_reply":"...", "reply_text":"...", "username":"..."}'
            "إذا وجدتِ 'راسلني' أو 'راسل @username' بعد فوز، استخدمي contact_winner وحددي username. "
            "إذا كانت 'أول شخص يكتب...' استخدمي safe_contest. "
            "إذا كانت 'اكثر نجوم' استخدمي dangerous_contest. "
            "إذا كانت أزرار روليت/سحب استخدمي hunt. "
            "إذا كانت محادثة عادية، استخدمي reply مع رد لطيف."
        )
        try:
            resp = ollama.chat(model=OLLAMA_MODEL,
                               messages=[{"role":"system","content":system},
                                         {"role":"user","content":f"الذاكرة:\n{context}\n\nالرسالة:\n{text}"}],
                               format="json", options={"temperature":0.7, "max_tokens":150})
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
            thanks = random.choice(["يسلمووو ❤️","تسلم يالغالي 🌸","واااي شكراً 💫","يدك مبدوءة بالخير 💝"])
            await asyncio.sleep(random.uniform(2,5))
            try: await event.reply(thanks)
            except: pass
            return True
        return False

    # ---------- تحويل هدايا عادية ----------
    async def convert_gift(self, event):
        if event.reply_markup and any(w in (event.raw_text or "") for w in ['هدية من','أضاف','الهدية']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل','نجمة','convert','stars']):
                        await event.click(row.row_index, btn.column_index)
                        self.stats['gifts_converted'] += 1
                        self.stats['stars'] += random.randint(10,50)
                        await self.update_stats_msg()
                        try: await event.client(DeleteHistoryRequest(peer=event.chat_id, max_id=0, just_clear=True))
                        except: pass
                        return True
        return False

    # ---------- صيد الأزرار ----------
    async def hunt_buttons(self, event, client):
        if not event.reply_markup: return
        for r,row in enumerate(event.reply_markup.rows):
            for b,btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r,b)
                        self.stats['wins'] += 1
                        self.stats['stars'] += random.randint(1,5)
                        if not self.sniper_enabled and self.stats['stars']>=100: self.sniper_enabled=True
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

    # ---------- مراسلة الفائز ----------
    async def contact_winner(self, event, client, username):
        try:
            await client.send_message(username, "أنا الفائزة")
            logger.info(f"تمت مراسلة {username}")
        except Exception as e:
            logger.warning(f"فشل مراسلة {username}: {e}")

    # ---------- معالجة الرسالة الأساسية ----------
    async def process(self, event, client):
        if not self.running: return
        self.stats['msgs_processed'] += 1

        # 1. هدايا النجوم الحقيقية
        if await self.handle_star_gift(event, client): return

        # 2. تحويل هدايا عادية
        if await self.convert_gift(event): return

        text = event.raw_text or ""

        # 3. تحليل AI
        decision = await self.analyze(text)
        action = decision.get("action", "ignore")

        # 4. تنفيذ
        if action == "dangerous_contest": return
        if action == "safe_contest":
            reply = decision.get("contest_reply", "تم")
            try: await event.reply(reply)
            except: pass
            if event.reply_markup: await self.hunt_buttons(event, client)
        elif action == "contact_winner":
            username = decision.get("username")
            if username: await self.contact_winner(event, client, username)
        elif action == "hunt" or (event.reply_markup and event.id not in self.cache):
            if event.reply_markup and event.id not in self.cache:
                btn_texts = "".join(b.text for r in event.reply_markup.rows for b in r.buttons)
                if any(k in (text + btn_texts).lower() for k in HUNT_KEYWORDS):
                    self.cache.add(event.id)
                    await self.auto_join(event, client)
                    await asyncio.sleep(random.uniform(2,6))
                    await self.hunt_buttons(event, client)
        elif action == "reply" and event.is_private:
            reply_text = decision.get("reply_text")
            if reply_text:
                await asyncio.sleep(random.uniform(5,20))
                try: await client(ReadHistoryRequest(peer=event.chat_id, max_id=event.id))
                except: pass
                await asyncio.sleep(random.uniform(1.5,3))
                async with client.action(event.chat_id, 'typing'):
                    await asyncio.sleep(random.uniform(1,3))
                try: await event.reply(reply_text)
                except: pass

        # تحديث الذاكرة (للتعلم)
        if len(text) > 5 and len(text) < 150:
            self.memory.append(text[:100])
            if len(self.memory) > MAX_MEMORY: self.memory.pop(0)
            self.save_memory()

        await self.update_stats_msg()

    # ---------- تغيير شخصية الحساب الثاني فقط ----------
    async def persona_changer(self):
        while self.running:
            await asyncio.sleep(3600)
            if self.c2 and self.sniper_enabled and (datetime.now()-self.last_persona_change).total_seconds() > random.randint(70000,100000):
                name = random.choice(PERSONA_NAMES)
                bio = random.choice(PERSONA_BIOS)
                await self.c2(UpdateProfileRequest(first_name=name, about=bio))
                self.last_persona_change = datetime.now()
                logger.info(f"🔄 الحساب 2 تحول إلى {name}")

    # ---------- مغادرة القنوات الميتة ----------
    async def leave_dead(self):
        count = 0
        for client in [self.c1, self.c2] if self.c2 else [self.c1]:
            async for d in client.iter_dialogs():
                if not d.is_channel: continue
                try:
                    m = await client.get_messages(d.entity, limit=1)
                    if not m or not m[0].date or (datetime.now(tz=None)-m[0].date.replace(tzinfo=None)).days > 1:
                        await client(LeaveChannelRequest(d.entity)); count += 1
                except: pass
        self.stats['channels_left'] += count
        if count: await self.update_stats_msg()

    # ---------- الأوامر ----------
    async def handle_command(self, event, parts):
        cmd = parts[0][1:].lower(); args=parts[1:]
        try:
            if cmd=="stats": await self.update_stats_msg(); await event.reply("✅ تم")
            elif cmd=="stop": self.running=False; await event.reply("🛑")
            elif cmd=="start": self.running=True; await event.reply("✅")
            elif cmd=="sniper_on": self.sniper_enabled=True; await event.reply("🎯")
            elif cmd=="sniper_off": self.sniper_enabled=False; await event.reply("🎯")
            elif cmd=="leavedead":
                await self.leave_dead(); await event.reply("🧹")
            elif cmd=="panel":
                btns = [[Button.inline(".stats",b"stats"), Button.inline(".stop",b"stop")]]
                await event.respond("🔥 لوحة فاطمة", buttons=btns)
        except Exception as e: await event.reply(f"خطأ: {e}")

    # ---------- التشغيل الرئيسي ----------
    async def main(self):
        if not await self.iron_connect(self.c1, "حساب 1"): return
        self.main_client = self.c1
        if self.c2 and await self.iron_connect(self.c2, "حساب 2"):
            # الحساب الثاني يغير اسمه، لا نستخدمه كـ main_client
            pass
        else:
            self.c2 = None

        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id==ADMIN_ID and e.raw_text.startswith("."): await self.handle_command(e, e.raw_text.split())
            else: await self.process(e, self.c1)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e): await self.process(e, self.c2)

        asyncio.create_task(self.keep_alive(self.c1, "حساب 1"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2, "حساب 2"))
        asyncio.create_task(self.persona_changer())

        async def periodic():
            while self.running:
                await asyncio.sleep(14400)  # كل 4 ساعات
                await self.leave_dead()
        asyncio.create_task(periodic())

        await self.update_stats_msg()
        await self.c1(UpdateStatusRequest(offline=False))
        logger.info("🚀 فاطمة الزهراء انطلقت (حسابين)")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(FatimaBot().main())
