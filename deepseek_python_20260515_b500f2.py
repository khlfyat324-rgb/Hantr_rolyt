#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
فاطمة الزهراء – الإصدار الأسطوري مفتوح المصدر
Ollama + LLaMA3 8B | شخصية بنت 18 | تحكم كامل
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, asyncio, random, re, json, logging, time
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button, functions
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ReadHistoryRequest, DeleteHistoryRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.errors import AuthKeyDuplicatedError, FloodWaitError
import ollama

# --------------------------- إعداد السجل ---------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Fatima")

# --------------------------- المتغيرات البيئية ---------------------------
API_ID_1 = int(os.environ["API_ID_1"])
API_HASH_1 = os.environ["API_HASH_1"]
SESSION_1 = os.environ["SESSION_1"]
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "")
ADMIN_ID = int(os.environ["ADMIN_ID"])
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:8b")  # النموذج المفتوح

# --------------------------- ثوابت الشخصية ---------------------------
HUNT_KEYWORDS = ["مشاركة", "انضمام", "سحب", "دخول", "روليت", "دب", "هدية", "نجوم",
                 "تعزيز", "يلا", "سجل", "اضغط", "بسرعة", "التحق", "تأكيد", "شارك", "انقر"]
DANGER_WORDS = ["أكثر نجوم", "من يضع", "تصويت بنجوم", "اكثر شخص يحط", "يحط يربح", "مزاد نجوم"]
SAFE_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'
PERSONA_NAMES = ["فاطمة الزهراء", "لارا", "ملاك", "ليل", "سما", "روح", "فراشة", "نور"]
PERSONA_BIOS = ["لاعبة كرة ⚽ | 18 سنة", "بنت بسيطة تعشق الكورة", "مزاجي كرة وسهر 🌙"]

STATS_MSG_ID = None   # لتخزين معرف رسالة الإحصائيات في المحفوظات

# --------------------------- فئة السكربت ---------------------------
class FatimaBot:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stars = 0
        self.sniper_enabled = False
        self.last_persona = datetime.min
        self.cache = set()
        self.gift_log = []
        self.stats = {"wins":0, "stars":0, "gifts_bought":0, "gifts_converted":0, "channels_left":0, "start":time.time()}
        self.main_client = None

    # ---------- الاتصال الحديدي ----------
    async def iron_connect(self, client, name):
        for _ in range(10):
            try:
                await client.connect()
                if await client.is_user_authorized():
                    logger.info(f"✅ {name}")
                    return True
            except AuthKeyDuplicatedError:
                await client.disconnect(); await asyncio.sleep(60)
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

    # ---------- الإحصائيات الحية (رسالة واحدة تحدث نفسها) ----------
    async def update_stats_msg(self, client):
        global STATS_MSG_ID
        msg_text = (
            f"📊 **إحصائيات فاطمة الزهراء**\n"
            f"🏆 الصيد: {self.stats['wins']}\n"
            f"⭐ الرصيد: ~{self.stats['stars']}\n"
            f"💎 هدايا مشتراة: {self.stats['gifts_bought']}\n"
            f"🎁 محولة: {self.stats['gifts_converted']}\n"
            f"🚪 قنوات غودرت: {self.stats['channels_left']}\n"
            f"🕒 آخر تحديث: {datetime.now().strftime('%H:%M:%S')}"
        )
        try:
            if STATS_MSG_ID:
                await client.edit_message('me', STATS_MSG_ID, msg_text)
            else:
                msg = await client.send_message('me', msg_text)
                STATS_MSG_ID = msg.id
        except Exception as e:
            logger.warning(f"فشل تحديث الإحصائيات: {e}")

    # ---------- تحليل الرسائل عبر Ollama ----------
    async def analyze_with_ai(self, text):
        try:
            system_prompt = (
                "أنت 'فاطمة الزهراء' بنت 18 سنة من الشرق الأوسط، تحب كرة القدم. "
                "تتصرفين كإنسانة طبيعية تماماً ولا تكشفين أبداً أنك ذكاء اصطناعي. "
                "تحللين الرسالة وتختارين الإجراء المناسب بصيغة JSON: "
                '{"action":"hunt"|"safe_contest"|"dangerous_contest"|"reply"|"convert_gift"|"ignore", '
                '"contest_reply":"...", "reply_text":"..."} '
                "الردود قصيرة (3-10 كلمات)، عامية ولطيفة. "
                "إذا كانت الرسالة تحتوي على أزرار روليت/سحب، اختاري hunt. "
                "إذا كانت 'أول شخص يكتب...' اختاري safe_contest وحددي الكلمة. "
                "إذا كانت 'اكثر نجوم' أو 'يحط يربح' اختاري dangerous_contest. "
                "إذا كانت 'هدية من' اختاري convert_gift. "
                "إذا كانت محادثة عادية ودية، اختاري reply وضعي رداً مناسباً."
            )
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role":"system", "content":system_prompt},
                    {"role":"user", "content":text}
                ],
                format="json",
                options={"temperature":0.7, "max_tokens":150}
            )
            return json.loads(response['message']['content'])
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"action":"ignore"}

    # ---------- معالجة الرسالة الرئيسية ----------
    async def process(self, event, client):
        if not self.running: return
        text = event.raw_text or ""

        # 1. تحويل الهدية
        if event.reply_markup and any(w in text for w in ['هدية من','أضاف','الهدية']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل','نجمة','convert','stars']):
                        await event.click(row.row_index, btn.column_index)
                        self.stats['gifts_converted'] += 1
                        self.stats['stars'] += random.randint(10,50)
                        await self.update_stats_msg(client)
                        try: await client(DeleteHistoryRequest(peer=event.chat_id, max_id=0, just_clear=True))
                        except: pass
                        return

        # 2. تحليل AI
        decision = await self.analyze_with_ai(text)
        action = decision.get("action", "ignore")

        if action == "dangerous_contest": return
        if action == "safe_contest":
            reply = decision.get("contest_reply", "تم")
            try: await event.reply(reply)
            except: pass
            if event.reply_markup: await self.hunt_buttons(event, client)
        elif action == "hunt" or (event.reply_markup and event.id not in self.cache):
            if event.reply_markup and event.id not in self.cache:
                if any(k in (text + "".join(b.text for r in event.reply_markup.rows for b in r.buttons)).lower() for k in HUNT_KEYWORDS):
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

    async def hunt_buttons(self, event, client):
        if not event.reply_markup: return
        for r,row in enumerate(event.reply_markup.rows):
            for b,btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r,b)
                        self.stats['wins'] += 1
                        self.stats['stars'] += random.randint(1,5)
                        if not self.sniper_enabled and self.stats['stars']>=100:
                            self.sniper_enabled = True
                        await self.update_stats_msg(client)
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

    # ---------- الأوامر ----------
    async def handle_command(self, event, parts, client):
        cmd = parts[0][1:].lower(); args=parts[1:]
        try:
            if cmd=="panel":
                btns=[[Button.inline(".status",b"copy_status"), Button.inline(".stats",b"copy_stats")]]
                await event.respond("🔥 لوحة التحكم", buttons=btns)
            elif cmd=="stats":
                await self.update_stats_msg(client)
                await event.reply("✅ تم تحديث الإحصائيات")
            elif cmd=="stop": self.running=False; await event.reply("🛑")
            elif cmd=="start": self.running=True; await event.reply("✅")
            elif cmd=="sniper_on": self.sniper_enabled=True; await event.reply("🎯")
            elif cmd=="sniper_off": self.sniper_enabled=False; await event.reply("🎯")
            elif cmd=="leavedead":
                c=0
                async for d in client.iter_dialogs():
                    if not d.is_channel: continue
                    try:
                        m=await client.get_messages(d.entity,limit=1)
                        if not m or not m[0].date: await client(LeaveChannelRequest(d.entity)); c+=1
                    except: pass
                self.stats['channels_left']+=c
                await event.reply(f"🧹 {c}")
                await self.update_stats_msg(client)
        except Exception as e: await event.reply(f"خطأ: {e}")

    async def main(self):
        if not await self.iron_connect(self.c1,"ح1"): return
        self.main_client = self.c1
        if self.c2 and await self.iron_connect(self.c2,"ح2"): self.main_client = self.c2
        client = self.main_client

        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id==ADMIN_ID and e.raw_text.startswith("."): await self.handle_command(e, e.raw_text.split(), self.c1)
            else: await self.process(e, self.c1)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e): await self.process(e, self.c2)

        asyncio.create_task(self.keep_alive(self.c1,"ح1"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2,"ح2"))

        # أول تحديث للإحصائيات
        await self.update_stats_msg(client)
        await client(UpdateStatusRequest(offline=False))
        logger.info("🚀 فاطمة الزهراء (Ollama) انطلقت")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(FatimaBot().main())