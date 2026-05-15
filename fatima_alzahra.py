#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
فاطمة الزهراء – الإصدار النهائي 100%
نموذج Groq llama-3.3-70b-versatile | ردود احتياطية ذكية | جلسات حصرية
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
logger = logging.getLogger("FatimaV100")

# ---------- الإعدادات ----------
API_ID_1 = int(os.environ["API_ID_1"]); API_HASH_1 = os.environ["API_HASH_1"]; SESSION_1 = os.environ["SESSION_1"]
API_ID_2 = int(os.environ.get("API_ID_2", 0)); API_HASH_2 = os.environ.get("API_HASH_2", ""); SESSION_2 = os.environ.get("SESSION_2", "")
ADMIN_ID = int(os.environ["ADMIN_ID"])
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

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
        self.conversations = {}
        self.is_resting = False
        self.ai = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.ai_fail_count = 0
        self.ai_paused_until = None

    async def iron_connect(self, client, name):
        try:
            await client.connect()
            if await client.is_user_authorized():
                logger.info(f"✅ {name}")
                return True
        except AuthKeyDuplicatedError:
            logger.critical(f"🔑 {name} جلسة مكررة! لا تستخدم الحساب من مكان آخر.")
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

    def get_conv(self, uid):
        if uid not in self.conversations: self.conversations[uid] = []
        return self.conversations[uid]

    def add_conv(self, uid, role, text):
        c = self.get_conv(uid); c.append({"role":role,"text":text})
        if len(c) > 20: c.pop(0)

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
                sent = await self.main_client.send_message('me', msg); STATS_MSG_ID = sent.id
        except: pass

    # ---------- معالجة القنوات والمجموعات (سريع) ----------
    async def handle_public_message(self, event, client):
        text = event.raw_text or ""
        # تحويل الهدايا
        if event.reply_markup and any(w in text for w in ['هدية من','أضاف','الهدية']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل','نجمة','convert','stars']):
                        await event.click(row.row_index, btn.column_index)
                        self.stats['gifts_converted'] += 1; self.stats['stars'] += random.randint(10,50)
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
            if event.reply_markup: await self.hunt_buttons(event, client)
            return
        if event.reply_markup and event.id not in self.cache:
            btn_text = "".join(b.text for r in event.reply_markup.rows for b in r.buttons)
            if any(k in (text + " " + btn_text).lower() for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self.auto_join(event, client)
                await asyncio.sleep(random.uniform(1.5, 4))
                await self.hunt_buttons(event, client)
                return
        await self.snipe_gifts(event, client)

    # ---------- الرسائل الخاصة (AI) ----------
    async def handle_private_message(self, event, client):
        if event.out: return
        text = event.raw_text or ""
        uid = event.sender_id

        if isinstance(event.message.action, types.MessageActionStarGift):
            if event.reply_markup:
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if any(k in btn.text for k in ['تحويل','نجمة','convert']):
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_converted'] += 1; self.stats['stars'] += random.randint(10,50)
                            await self.update_stats_msg()
            thanks = random.choice(["يسلمووو ❤️","تسلم يالغالي 🌸","واااي شكراً 💫"])
            await asyncio.sleep(random.uniform(1,2))
            try: await event.reply(thanks)
            except: pass
            return

        self.add_conv(uid, "user", text)
        reply_text = await self.smart_reply(text, uid, event)
        if reply_text:
            await asyncio.sleep(random.uniform(2,5))
            try: await client(ReadHistoryRequest(peer=event.chat_id, max_id=event.id))
            except: pass
            await asyncio.sleep(random.uniform(0.5,1.5))
            async with client.action(event.chat_id, 'typing'):
                await asyncio.sleep(random.uniform(0.8,2))
            try: await event.reply(reply_text)
            except: pass

    async def smart_reply(self, user_text, uid, event):
        if self.ai_paused_until and datetime.now() < self.ai_paused_until:
            return self._fallback_reply(user_text)
        if self.ai_fail_count >= 3:
            self.ai_paused_until = datetime.now() + timedelta(minutes=5)
            self.ai_fail_count = 0
            logger.warning("⏳ إيقاف AI 5 دقائق")
            return self._fallback_reply(user_text)

        try:
            sender = await event.get_sender()
            sender_name = sender.first_name or "صاحبي"
            conv = self.get_conv(uid)
            history = "\n".join([f"{'هي' if m['role']=='assistant' else sender_name}: {m['text']}" for m in conv[-5:]])
            system_prompt = (
                "أنتِ 'فاطمة الزهراء'، بنت مغربية 18 سنة، لاعبة كرة. "
                "شخصيتك: لطيفة، خجولة شوي، تتكلمين العامية حسب الشخص. "
                "ردودك قصيرة (3-12 كلمة). لا تكرري نفس الكلام. لا تقولي 'غالي' مع الذكور. "
                "كوني طبيعية جداً. ردي بصيغة JSON: {\"reply_text\": \"...\"}"
            )
            response = await self.ai.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":system_prompt},
                         {"role":"user","content":f"تاريخ:\n{history}\n\nالرسالة:\n{user_text}"}],
                temperature=0.9, max_tokens=50,
                response_format={"type":"json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            reply = data.get("reply_text")
            if not reply: raise ValueError("empty")
            self.add_conv(uid, "assistant", reply)
            self.ai_fail_count = 0
            return reply
        except Exception as e:
            logger.error(f"Groq فشل ({self.ai_fail_count+1}): {e}")
            self.ai_fail_count += 1
            if self.ai_fail_count >= 3:
                self.ai_paused_until = datetime.now() + timedelta(minutes=5)
            return self._fallback_reply(user_text)

    def _fallback_reply(self, text):
        """ردود احتياطية ذكية ومتنوعة"""
        if any(w in text for w in ['مرحبا','سلام','اهلا','مساء']):
            return random.choice(["أهلاً وسهلاً 🌸","هلا والله","مراحب","مساء النور"])
        if 'كيفك' in text or 'شخبارك' in text:
            return random.choice(["الحمد لله بخير","تمام شكراً، ونتا؟","بخير الحمدلله"])
        if 'ش ع ت' in text or 'شنو' in text:
            return random.choice(["والو","مفهمتش واش قصدك؟","واش معنى؟"])
        return random.choice(["🌸","❤️","هلا","أهلاً","كيف داير؟"])

    # ---------- القناص (يشتري هدايا 80-150 نجمة) ----------
    async def snipe_gifts(self, event, client):
        if not self.sniper_enabled or not event.reply_markup: return
        text = event.raw_text or ""
        prices = re.findall(r'(?:سعر|ثمن|بيع|price|قيمة)\s*[:#]?\s*(\d{2,})', text, re.I)
        for p_str in prices:
            price = int(p_str)
            if 80 <= price <= 150 and self.stars >= price:
                gift = "هدية"; m = re.search(r'(?:هدية|Gift|مقتني)\s*["\']?([\w\s]+)', text, re.I)
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

    async def hunt_buttons(self, event, client):
        if not event.reply_markup: return
        for r,row in enumerate(event.reply_markup.rows):
            for b,btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r,b); self.stats['wins'] += 1; self.stats['stars'] += random.randint(1,5)
                        if not self.sniper_enabled and self.stars >= 100: self.sniper_enabled = True
                        await self.update_stats_msg(); return
                    except FloodWaitError as e: await asyncio.sleep(e.seconds+1)
                    except: pass

    async def auto_join(self, event, client):
        links = set()
        if event.entities:
            for e in event.entities:
                if hasattr(e,'url') and 't.me' in (e.url or ''): links.add(e.url)
        links.update(re.findall(r't\.me/[\w\d_]+|@[\w\d_]+', event.raw_text))
        for l in links:
            name=l.split('/')[-1].replace('@','')
            try: await client(JoinChannelRequest(name))
            except: pass

    async def handle_command(self, event, parts):
        cmd = parts[0][1:].lower()
        if cmd=="stats": await self.update_stats_msg(); await event.reply("✅")
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
            await event.respond("🔥 أوامر", buttons=[Button.inline(".stats",b"stats")])

    async def main(self):
        if not await self.iron_connect(self.c1, "ح1"): return
        self.main_client = self.c1
        if self.stars >= 100: self.sniper_enabled = True
        if self.c2 and not await self.iron_connect(self.c2, "ح2"): self.c2 = None

        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id==ADMIN_ID and e.raw_text.startswith("."):
                await self.handle_command(e, e.raw_text.split())
            elif e.is_private:
                await self.handle_private_message(e, self.c1)
            else:
                if self.running and not self.is_resting:
                    self.stats['msgs_processed'] += 1
                    await self.handle_public_message(e, self.c1)
                    if self.stats['msgs_processed'] % 5 == 0: await self.update_stats_msg()

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e):
                if e.is_private: await self.handle_private_message(e, self.c2)
                elif self.running and not self.is_resting: await self.handle_public_message(e, self.c2)

        asyncio.create_task(self.keep_alive(self.c1,"ح1"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2,"ح2"))
        asyncio.create_task(self.rest_schedule())

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
        logger.info("🚀 فاطمة (نهائية) انطلقت")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(FatimaBot().main())
