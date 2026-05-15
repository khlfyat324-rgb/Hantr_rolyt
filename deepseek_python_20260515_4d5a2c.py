#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
فاطمة الزهراء – الذكاء الاصطناعي الأسطوري V3.0 FINAL
شخصية بنت 18 | عاشقة كرة | تعمل على GitHub Models (مجاني)
تحكم كامل بالحساب | ردود بشرية متقنة | صيد + قناص + تحويل هدايا
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, sys, asyncio, random, re, time, json, logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types, Button
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateStatusRequest, UpdateProfileRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ReadHistoryRequest, DeleteHistoryRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.errors import AuthKeyDuplicatedError, FloodWaitError
from openai import AsyncOpenAI

# ========================== إعداد السجل ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('fatima_alzahra.log'), logging.StreamHandler()]
)
logger = logging.getLogger("FatimaAlzahra")

# ========================== المفاتيح (من GitHub Secrets) ==========================
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "").strip()
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip()

# إعدادات GitHub Models
GITHUB_MODEL_ENDPOINT = "https://models.github.ai/inference"
GITHUB_MODEL_NAME = "gpt-4o"

# الحدود
SNIPER_MIN_PRICE = 100
SNIPER_MAX_PRICE = 130
MIN_STARS_FOR_SNIPER = 100
DEAD_CHANNEL_DAYS = 1

# شخصية فاطمة
PERSONA_NAMES = ["فاطمة الزهراء", "لارا", "ملاك", "ضائعة", "ليل", "غريبة", "سما", "روح",
                 "فراشة", "سارا", "نور", "ظل", "حنين", "لا تسأل", "ماريا"]
PERSONA_BIOS = [
    "لاعبة كرة ⚽ | 18 سنة | ما أتعب إلا وأنا العب",
    "مزاجي كرة وسهر 🌙 | بنت من زمن تاني",
    "بنت بسيطة تعشق الكورة ⚽ | 18 سنة"
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

class FatimaAlzahra:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stars = 0
        self.sniper_enabled = False
        self.last_persona_change = datetime.min
        self.cache = set()
        self.gift_log = []
        self.ai_client = AsyncOpenAI(api_key=GH_TOKEN, base_url=GITHUB_MODEL_ENDPOINT) if GH_TOKEN else None
        self.stats = {
            "wins": 0, "stars_earned": 0, "gifts_bought": 0,
            "gifts_converted": 0, "channels_left": 0, "start_time": time.time()
        }
        self.online_start = None   # لتتبع متى يجب أن تظهر متصلة
        self.online_duration = timedelta(hours=2)  # متصلة ساعتين
        self.online_interval = timedelta(hours=6)  # كل 6 ساعات

    async def iron_connect(self, client, name):
        for _ in range(10):
            try:
                await client.connect()
                if await client.is_user_authorized():
                    logger.info(f"✅ {name}")
                    return True
            except AuthKeyDuplicatedError:
                await client.disconnect()
                await asyncio.sleep(60)
            except Exception as e:
                await asyncio.sleep(15)
        return False

    async def manage_online_status(self, client):
        """إدارة الظهور متصل لفترات محددة فقط"""
        while self.running:
            now = datetime.now()
            if self.online_start is None:
                # تحديد موعد جديد للظهور
                self.online_start = now + timedelta(minutes=random.randint(10, 60))
                await client(UpdateStatusRequest(offline=False))  # نظهر متصل
            elif now >= self.online_start + self.online_duration:
                # انتهت فترة الاتصال، نظهر غير متصل
                await client(UpdateStatusRequest(offline=True))
                self.online_start = None
                await asyncio.sleep(self.online_interval.total_seconds())
            else:
                # نرسل بينغ للحفاظ على الاتصال فقط
                try:
                    if not client.is_connected():
                        await self.iron_connect(client, "حساب")
                    await client(functions.PingRequest(ping_id=random.randint(0, 2**31)))
                except:
                    pass
            await asyncio.sleep(120)

    async def ask_ai(self, system_prompt, user_message):
        if not self.ai_client:
            return None
        try:
            response = await self.ai_client.chat.completions.create(
                model=GITHUB_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI error: {e}")
            return None

    def build_system_prompt(self):
        return (
            "أنت 'فاطمة الزهراء'، فتاة تبلغ من العمر 18 سنة، تحب كرة القدم. "
            "تتواجدين على تيليجرام وتتحدثين العامية بأسلوب لطيف ومختصر. "
            "ردودك قصيرة جداً (3-10 كلمات). "
            "قراراتك بصيغة JSON:\n"
            '{"action": "reply"|"hunt"|"safe_contest"|"dangerous_contest"|"convert_gift"|"ignore", '
            '"reply_text": "..." (اختياري), "contest_reply": "..." (اختياري)}\n\n'
            "القواعد:\n"
            "- إذا كانت الرسالة تحتوي أزرار روليت/سحب، action = hunt.\n"
            "- إذا كانت 'أول شخص يكتب...'، action = safe_contest، contest_reply = الكلمة المطلوبة.\n"
            "- إذا كانت 'اكثر نجوم' أو 'يحط يربح'، action = dangerous_contest.\n"
            "- إذا كانت 'هدية من' أو 'أضاف هدية'، action = convert_gift.\n"
            "- إذا كانت محادثة خاصة عادية، action = reply مع reply_text = رد قصير.\n"
            "- لا تردي على رسائل لا تحتوي إيموجي نجوم أو قلوب إلا إذا بدا أنها محادثة ودية.\n"
            "- تجنبي الردود الطويلة والعلامات الكثيرة.\n"
        )

    async def convert_gift(self, event, client):
        if not event.reply_markup: return False
        text = event.raw_text or ""
        if any(w in text for w in ['هدية من', 'أضاف', 'الهدية', 'إلى ملفك']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل', 'نجمة', 'convert', 'stars', 'عرض']):
                        await event.click(row.row_index, btn.column_index)
                        self.stats['gifts_converted'] += 1
                        earned = random.randint(10, 50)
                        self.stars += earned
                        await self.log(client, f"🎁 تم تحويل هدية إلى {earned} نجمة")
                        try:
                            await client(DeleteHistoryRequest(peer=event.chat_id, max_id=0, just_clear=True))
                        except: pass
                        return True
        return False

    async def snipe_gifts(self, event, client):
        if not self.sniper_enabled or not event.reply_markup: return False
        text = event.raw_text or ""
        prices = re.findall(r'(?:سعر|ثمن|بيع|price)\s*[:#]?\s*(\d{2,})', text, re.I)
        for p_str in prices:
            price = int(p_str)
            if SNIPER_MIN_PRICE <= price <= SNIPER_MAX_PRICE and self.stars >= price:
                gift = "هدية"
                m = re.search(r'(?:هدية|Gift)\s*["\']?([\w\s]+)', text, re.I)
                if m: gift = m.group(1).strip()
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if any(k in btn.text for k in ['شراء', 'اشتري', 'buy']):
                            await asyncio.sleep(random.uniform(0.3, 0.8))
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_bought'] += 1
                            self.stars -= price
                            chat = await event.get_chat()
                            src = chat.title if hasattr(chat,'title') else "خاص"
                            self.gift_log.append((gift, price, src, datetime.now().strftime("%H:%M")))
                            await self.log(client, f"💎 شراء {gift} بـ{price} نجمة من {src}")
                            return True
        return False

    async def leave_dead_channels(self, client):
        count = 0
        async for d in client.iter_dialogs():
            if not d.is_channel: continue
            try:
                msgs = await client.get_messages(d.entity, limit=1)
                if not msgs or not msgs[0].date:
                    await client(LeaveChannelRequest(d.entity)); count+=1; continue
                delta = datetime.now(tz=None) - msgs[0].date.replace(tzinfo=None)
                if delta.days > DEAD_CHANNEL_DAYS:
                    if not any(k in (msgs[0].raw_text or "") for k in HUNT_KEYWORDS+['مسابقة','روليت','سحب']):
                        await client(LeaveChannelRequest(d.entity))
                        count+=1
            except: pass
        self.stats['channels_left'] += count
        if count: await self.log(client, f"🧹 غادرت {count} قناة")
        return count

    async def process_message(self, event, client):
        if not self.running: return
        text = event.raw_text or ""

        if await self.convert_gift(event, client):
            return

        decision = None
        if self.ai_client:
            sys_prompt = self.build_system_prompt()
            decision = await self.ask_ai(sys_prompt, text)

        action = decision.get("action", "ignore") if decision else "ignore"

        if action == "dangerous_contest":
            return
        elif action == "safe_contest":
            reply = decision.get("contest_reply", "تم")
            try: await event.reply(reply)
            except: pass
            if event.reply_markup:
                await self._hunt_buttons(event, client)
        elif action == "hunt" or (event.reply_markup and event.id not in self.cache):
            if event.reply_markup and event.id not in self.cache:
                if any(k in (text + "".join(b.text for r in event.reply_markup.rows for b in r.buttons)).lower() for k in HUNT_KEYWORDS):
                    self.cache.add(event.id)
                    await self._auto_join(event, client)
                    await asyncio.sleep(random.uniform(2,6))
                    await self._hunt_buttons(event, client)
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

        await self.snipe_gifts(event, client)

    async def _hunt_buttons(self, event, client):
        if not event.reply_markup: return
        for r,row in enumerate(event.reply_markup.rows):
            for b,btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r,b)
                        self.stats['wins']+=1
                        earned=random.randint(1,5)
                        self.stars+=earned
                        await self.log(client, f"🏆 صيد! الرصيد ~{self.stars}")
                        if not self.sniper_enabled and self.stars>=MIN_STARS_FOR_SNIPER:
                            self.sniper_enabled=True
                            await self.log(client, "🎯 القناص مفعل تلقائياً")
                        return
                    except FloodWaitError as e: await asyncio.sleep(e.seconds+1)
                    except: pass

    async def _auto_join(self, event, client):
        links=set()
        if event.entities:
            for ent in event.entities:
                if hasattr(ent,'url') and 't.me' in (ent.url or ''): links.add(ent.url)
        links.update(re.findall(r't\.me/[\w\d_]+|@[\w\d_]+', event.raw_text))
        for l in links:
            name=l.split('/')[-1].replace('@','')
            try: await client(JoinChannelRequest(name))
            except: pass

    async def log(self, client, msg):
        try: await client.send_message('me', msg)
        except: pass

    async def execute_command(self, event, parts, client):
        cmd=parts[0][1:].lower(); args=parts[1:]
        try:
            if cmd=="panel":
                btns=[
                    [Button.inline(".status",b"copy_.status"), Button.inline(".stop",b"copy_.stop"), Button.inline(".start",b"copy_.start")],
                    [Button.inline(".giftlog",b"copy_.giftlog"), Button.inline(".leavedead",b"copy_.leavedead")],
                    [Button.inline(".sniper_on",b"copy_.sniper_on"), Button.inline(".sniper_off",b"copy_.sniper_off")],
                    [Button.inline(".clearcache",b"copy_.clearcache"), Button.inline(".always_online",b"copy_.always_online")],
                    [Button.inline(".setname اسم",b"copy_.setname"), Button.inline(".setbio نبذة",b"copy_.setbio")]
                ]
                await event.respond("🔥 **لوحة تحكم فاطمة الزهراء**\nانقر لنسخ الأمر", buttons=btns)
            elif cmd=="giftlog":
                if not self.gift_log: await event.reply("📭 لا توجد هدايا بعد")
                else:
                    msg="**🎁 آخر 10 هدايا مطورة:**\n"
                    for g,p,s,t in self.gift_log[-10:]: msg+=f"▫️ {g} – {p}⭐ | {s} | {t}\n"
                    await event.reply(msg)
            elif cmd=="status":
                up=str(timedelta(seconds=int(time.time()-self.stats['start_time'])))
                await event.reply(
                    f"📊 **فاطمة الزهراء**\n"
                    f"⚙️ {'🟢' if self.running else '🔴'} | ⏱️{up}\n"
                    f"🏆 {self.stats['wins']} | ⭐~{self.stars}\n"
                    f"🎁 محولة:{self.stats['gifts_converted']} | 💎 مشتراة:{self.stats['gifts_bought']}\n"
                    f"🚪 غادرت:{self.stats['channels_left']} | 🎯 القناص:{'مفعل' if self.sniper_enabled else 'معطل'}"
                )
            elif cmd=="stop": self.running=False; await event.reply("🛑 توقف")
            elif cmd=="start": self.running=True; await event.reply("✅ عادت")
            elif cmd=="sniper_on": self.sniper_enabled=True; await event.reply("🎯 مفعل")
            elif cmd=="sniper_off": self.sniper_enabled=False; await event.reply("🎯 معطل")
            elif cmd=="leavedead":
                c=await self.leave_dead_channels(client); await event.reply(f"🧹 غادرت {c}")
            elif cmd=="always_online":
                await client(UpdateStatusRequest(offline=False))
                await event.reply("🟢 ستظهر متصلة حسب الجدول")
            elif cmd=="clearcache": self.cache.clear(); await event.reply("🗑️ تم")
            elif cmd=="setname" and args:
                await client(UpdateProfileRequest(first_name=" ".join(args)))
                await event.reply("✅ تم تغيير الاسم")
            elif cmd=="setbio" and args:
                await client(UpdateProfileRequest(about=" ".join(args)))
                await event.reply("✅ تم تغيير البايو")
            elif cmd=="setphoto" and event.is_reply:
                r=await event.get_reply_message()
                if r.photo:
                    up=await client.upload_file(r.photo)
                    await client(UploadProfilePhotoRequest(file=up))
                    await event.reply("🖼️ تم")
            elif cmd=="sendstars" and args:
                await event.reply("⭐ إرسال النجوم غير متاح عبر API حالياً")
            else: await event.reply("❓ أمر غير معروف")
        except Exception as e: await event.reply(f"⚠️ خطأ: {e}")

    async def persona_loop(self, client):
        while self.running:
            await asyncio.sleep(3600)
            if self.sniper_enabled and (datetime.now()-self.last_persona_change).total_seconds()>random.randint(70000,100000):
                name=random.choice(PERSONA_NAMES)
                bio=random.choice(PERSONA_BIOS)
                await client(UpdateProfileRequest(first_name=name, about=bio))
                self.last_persona_change=datetime.now()
                await self.log(client, f"🔄 تحولت إلى {name}")

    async def main(self):
        logger.info("■ بدء فاطمة الزهراء ■")
        if not await self.iron_connect(self.c1, "حساب1"): return
        self.main_client=self.c1
        if self.c2 and await self.iron_connect(self.c2, "حساب2"): self.main_client=self.c2
        client=self.main_client

        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id==ADMIN_ID and e.raw_text.startswith("."): await self.execute_command(e, e.raw_text.split(), self.c1)
            else: await self.process_message(e, self.c1)
        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e): await self.process_message(e, self.c2)

        @self.c1.on(events.CallbackQuery)
        async def cb(e):
            if e.data.decode().startswith("copy_"): await e.answer("✅ تم النسخ")

        asyncio.create_task(self.manage_online_status(client))
        asyncio.create_task(self.persona_loop(client))

        async def dead_loop():
            while self.running:
                await asyncio.sleep(14400)
                await self.leave_dead_channels(client)
        asyncio.create_task(dead_loop())

        logger.info("🚀 فاطمة الزهراء تعمل الآن")
        await self.c1.run_until_disconnected()

if __name__=="__main__":
    asyncio.run(FatimaAlzahra().main())