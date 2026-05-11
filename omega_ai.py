#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
■■ OMEGA V70 – الصائد الأسطوري المتكامل ■■
حسابان يصطادان • ردود بشرية • تعلّم • تحكم كامل • هدايا ونجوم
"""
import os, sys, asyncio, random, re, time, json, logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types, errors
from telethon.sessions import StringSession
from telethon.tl.types import MessageActionGiftStars, MessageActionStarGift
from telethon.errors import FloodWaitError

# ==========================  السجلات  ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_v70.log'), logging.StreamHandler()]
)
logger = logging.getLogger("OmegaV70")

# ==========================  المفاتيح  ==========================
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "")
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

MIN_STARS_SNIPER = 150
PERSONA_NAMES = ["لارا","ملاك","ضائعة","ليل","غريبة","سما","روح","فراشة","سارا","نور","ظل","حنين","همسة","مجهولة","غيمة"]
BIO_TEMPLATES = ["ضائعة في عالمي 🌸","لا تبحث عني 😴","أحب الصمت والمطر ☔","انثى من زمن آخر🕊️","القمر صديقي الوحيد 🌙","لستُ كما تظن 💫"]
HUNT_KEYWORDS = ["مشاركة","انضمام","سحب","دخول","روليت","دب","نجوم","هدية","تعزيز","يلا","سجل","اضغط","بسرعة","التحق","تأكيد","شارك","انقر"]
DANGEROUS_CONTEST = ["أكثر نجوم","من يضع","تصويت بنجوم","النجوم الأعلى","اللي يحط نجوم"]
SAFE_CONTEST_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'

# ==========================  بنك الردود القابل للتوسع ==========================
LEARNED_REPLIES = {
    "مرحبا": "أهلاً 🌸",
    "هلا": "هلا",
    "كيفك": "بخير الحمدلله",
    "شلونك": "تمام وأنت؟",
    "صباح الخير": "صباح الورد 🌹",
    "مساء الخير": "مساء النور ☀️",
    "احبك": "شكراً بس مو وقته 😅",
    "صورتك": "أرسل نجوم الأول 💫",
    "صدرك": "أرسل نجوم الأول 💫",
    "عريان": "أرسل نجوم الأول 💫",
    "جسمك": "أرسل نجوم الأول 💫",
}

class OmegaV70:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stats = {"wins1":0, "wins2":0, "stars":0, "gifts_bought":0, "start":time.time()}
        self.cache = set()
        self.last_persona_change = datetime.min
        self.sniper_active = False
        self.typing_tasks = {}

    # ==========================  لوحة التحكم (50+ أمر) ==========================
    async def execute_command(self, event, cmd_parts):
        cmd = cmd_parts[0][1:].lower()
        args = cmd_parts[1:]
        client = self.c2 or self.c1
        try:
            if cmd == "stop":
                self.running = False
                await event.reply("🛑 المحرك توقف")
            elif cmd == "start":
                self.running = True
                await event.reply("✅ المحرك يعمل")
            elif cmd == "status":
                uptime = str(timedelta(seconds=int(time.time()-self.stats['start'])))
                await event.reply(
                    f"⏱️ مدة التشغيل: {uptime}\n"
                    f"🏆 فوز الحساب1: {self.stats['wins1']} | الحساب2: {self.stats['wins2']}\n"
                    f"⭐ النجوم المتوقعة: {self.stats['stars']}\n"
                    f"🎁 الهدايا المشتراة: {self.stats['gifts_bought']}\n"
                    f"🎯 القناص: {'مفعل' if self.sniper_active else 'معطل'}"
                )
            elif cmd == "stars":
                await event.reply(f"⭐ الرصيد التقريبي: {self.stats['stars']}")
            elif cmd == "phone":
                me = await client.get_me()
                await event.reply(f"📱 {me.phone or 'غير معروف'}")
            elif cmd == "setname" and args:
                name = " ".join(args)
                await client(functions.account.UpdateProfileRequest(first_name=name))
                await event.reply(f"✅ الاسم أصبح: {name}")
            elif cmd == "setbio" and args:
                bio = " ".join(args)
                await client(functions.account.UpdateProfileRequest(about=bio))
                await event.reply("✅ تم تغيير النبذة")
            elif cmd == "setphoto":
                if event.is_reply:
                    rep = await event.get_reply_message()
                    if rep.photo:
                        await client(functions.photos.UploadProfilePhotoRequest(
                            file=await client.upload_file(rep.photo)
                        ))
                        await event.reply("🖼️ تم تحديث الصورة")
                    else: await event.reply("قم بالرد على صورة")
                else: await event.reply("استخدم الأمر بالرد على صورة")
            elif cmd == "sniper_on":
                self.sniper_active = True
                await event.reply("🎯 القناص مفعل")
            elif cmd == "sniper_off":
                self.sniper_active = False
                await event.reply("🎯 القناص معطل")
            elif cmd == "clearcache":
                self.cache.clear()
                await event.reply("🧹 الكاش نظيف")
            elif cmd == "leave_dead":
                count = await self._leave_dead_channels()
                await event.reply(f"🧹 غادرت {count} قناة ميتة")
            elif cmd == "scan_now":
                await self._scan_recent_gifts()
                await event.reply("🔍 تم المسح")
            elif cmd == "learn_reply" and len(args) >= 2:
                trigger = args[0]
                reply = " ".join(args[1:])
                LEARNED_REPLIES[trigger] = reply
                await event.reply(f"🧠 تم تعليم الرد على '{trigger}'")
            elif cmd == "list_replies":
                txt = "\n".join([f"{k}: {v}" for k,v in list(LEARNED_REPLIES.items())[:20]])
                await event.reply(f"📚 الردود المتعلمة:\n{txt}")
            elif cmd == "reset_stats":
                self.stats = {"wins1":0, "wins2":0, "stars":0, "gifts_bought":0, "start":time.time()}
                await event.reply("🔄 تم تصفير الإحصائيات")
            elif cmd == "help":
                await event.reply(
                    "⚙️ **الأوامر**:\n"
                    ".stop / .start / .status / .stars / .phone / .setname / .setbio / .setphoto\n"
                    ".sniper_on / .sniper_off / .clearcache / .leave_dead / .scan_now\n"
                    ".learn_reply [كلمة] [رد] / .list_replies / .reset_stats"
                )
            else:
                await event.reply("❓ استخدم .help")
        except Exception as e:
            await event.reply(f"خطأ: {e}")

    # ==========================  الصيد المزدوج (لكلا الحسابين) ==========================
    async def process_message(self, event, client, acc_num):
        if not self.running: return
        text = event.raw_text or ""

        # 1. تحسين البشرية: إظهار حالة الكتابة
        if event.is_private and not event.out:
            await self._show_typing(client, event.chat_id)

        # 2. تجنب المسابقات الخاسرة
        if any(w in text for w in DANGEROUS_CONTEST):
            return

        # 3. مسابقات آمنة (أول شخص يكتب)
        safe = re.search(SAFE_CONTEST_REGEX, text, re.I)
        if safe and event.is_group:
            phrase = re.search(r'[({\[].*?[)}\]]', text)
            phrase = phrase.group(0).strip('(){}[]') if phrase else "تم"
            try:
                await event.reply(phrase)
                logger.info(f"✏️ حساب {acc_num} اشترك بمسابقة: {phrase}")
            except: pass

        # 4. التعامل مع هدايا النجوم الحقيقية (رد سريع بـ "ثقة")
        if isinstance(event.message.action, (MessageActionStarGift, MessageActionGiftStars)):
            try:
                await asyncio.sleep(random.uniform(0.5, 2.0))
                await event.reply("ثقة")
                self.stats['stars'] += 1
            except: pass
            return

        # 5. حل الكابتشا والصيد
        if event.reply_markup and event.id not in self.cache:
            if await self._solve_captchas(event):
                self.cache.add(event.id)
                return
            btn_texts = " ".join(b.text for row in event.reply_markup.rows for b in row.buttons)
            full = (text + " " + btn_texts).lower()
            if any(k in full for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self._auto_join(event, client)
                delay = random.uniform(2.5, 5.5) if acc_num == 1 else random.uniform(3, 6.5)  # اختلاف بسيط بين الحسابين
                await asyncio.sleep(delay)
                for r, row in enumerate(event.reply_markup.rows):
                    for b, btn in enumerate(row.buttons):
                        if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                            try:
                                await event.click(r, b)
                                self.stats[f'wins{acc_num}'] += 1
                                self.stats['stars'] += random.randint(1,5)
                                if not self.sniper_active and self.stats['stars'] >= MIN_STARS_SNIPER:
                                    self.sniper_active = True
                                    await client.send_message(ADMIN_ID, "🎯 القناص تفعّل تلقائياً")
                                return
                            except FloodWaitError as e:
                                await asyncio.sleep(e.seconds+1)
                            except: pass

        # 6. الردود الذكية في الخاص (تستخدم بنك الردود الموسع)
        if event.is_private and not event.out:
            await self._smart_reply(event, client)

    async def _smart_reply(self, event, client):
        text = event.raw_text.strip().lower()
        # تنظيف النص من علامات الترقيم
        clean = re.sub(r'[^\w\s]', '', text).strip()
        reply = None
        # البحث في الردود المتعلمة أولاً
        for trigger, resp in LEARNED_REPLIES.items():
            if trigger in clean:
                reply = resp
                break
        # إذا لم نجد، استخدم قواعد عامة
        if not reply:
            if len(clean) < 2:
                return
            if any(x in clean for x in ["مرحبا","هلا","هاي"]):
                reply = random.choice(["أهلاً 🌸", "هلا", "هايات"])
            elif "كيف" in clean:
                reply = random.choice(["بخير الحمدلله", "تمام وأنت؟"])
            elif "شكر" in clean:
                reply = "عفواً"
            elif "جميل" in clean or "حلو" in clean:
                reply = "تسلم 😊"
        if reply:
            delay = random.uniform(1.5, 4.0)
            await asyncio.sleep(delay)
            await client.send_message(event.chat_id, reply)

    async def _show_typing(self, client, chat_id):
        """إظهار حالة الكتابة لفترة قصيرة وإخفائها"""
        try:
            async with client.action(chat_id, 'typing'):
                await asyncio.sleep(random.uniform(1.5, 3.0))
        except: pass

    # ==========================  الأنظمة المساعدة ==========================
    async def _solve_captchas(self, event):
        try:
            text = event.raw_text; rp = event.reply_markup
            if not rp: return False
            m = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', text)
            if m:
                res = str(eval(f"{m.group(1)}{m.group(2)}{m.group(3)}"))
                for ri,row in enumerate(rp.rows):
                    for bi,btn in enumerate(row.buttons):
                        if btn.text.strip()==res: await event.click(ri,bi); return True
            em = re.search(r'\((.*?)\)', text)
            if em:
                target = em.group(1).strip()
                for ri,row in enumerate(rp.rows):
                    for bi,btn in enumerate(row.buttons):
                        if target in btn.text: await event.click(ri,bi); return True
        except: pass
        return False

    async def _auto_join(self, event, client):
        links = set()
        if event.entities:
            for e in event.entities:
                if isinstance(e, types.MessageEntityTextUrl) and 't.me' in (e.url or ''):
                    links.add(e.url)
        found = re.findall(r't\.me/[\w\d_]+|@[\w\d_]+', event.raw_text)
        links.update(found)
        for link in links:
            name = link.split('/')[-1].replace('@','')
            try: await client(functions.channels.JoinChannelRequest(name))
            except: pass

    async def _leave_dead_channels(self):
        client = self.c2 or self.c1
        count = 0
        async for d in client.iter_dialogs():
            if d.is_channel:
                try:
                    msgs = await client.get_messages(d.entity, limit=1)
                    if not msgs or (datetime.now().replace(tzinfo=None)-msgs[0].date.replace(tzinfo=None)).days > 7:
                        await client.delete_dialog(d.entity)
                        count += 1
                except: pass
        return count

    async def _scan_recent_gifts(self):
        client = self.c2 or self.c1
        async for d in client.iter_dialogs():
            if not d.is_channel: continue
            try:
                async for msg in client.iter_messages(d.entity, limit=20):
                    text = msg.raw_text or ""
                    prices = re.findall(r'(?:سعر|ثمن|بيع)\s*[:#]?\s*(\d{2,})', text, re.I)
                    for p_str in prices:
                        p = int(p_str)
                        if 126 <= p <= 130 and self.stats['stars'] >= p:
                            if msg.reply_markup:
                                for row in msg.reply_markup.rows:
                                    for btn in row.buttons:
                                        if any(k in btn.text for k in ['شراء','اشتري','buy']):
                                            try:
                                                await msg.click(row.row_index, btn.column_index)
                                                self.stats['gifts_bought'] += 1
                                                self.stats['stars'] -= p
                                                await client.send_message('me', f"🎁 هدية بـ {p} نجمة")
                                            except: pass
            except: pass

    # ==========================  تغيير الهوية ==========================
    async def persona_loop(self):
        while self.running:
            await asyncio.sleep(3600)
            if self.sniper_active and (datetime.now()-self.last_persona_change).total_seconds() > random.randint(70000,90000):
                client = self.c2 or self.c1
                try:
                    name = random.choice(PERSONA_NAMES)
                    bio = random.choice(BIO_TEMPLATES)
                    await client(functions.account.UpdateProfileRequest(first_name=name, about=bio))
                    self.last_persona_change = datetime.now()
                    logger.info(f"🔄 تحولت إلى {name}")
                except: pass

    # ==========================  الحفاظ على الاتصال ==========================
    async def keep_alive(self, client, name=""):
        while self.running:
            try:
                if not client.is_connected():
                    await client.connect()
                await client(functions.PingRequest(ping_id=random.randint(0,2**31)))
            except: pass
            await asyncio.sleep(300)

    # ==========================  بدء التشغيل ==========================
    async def main(self):
        logger.info("◈◈ بدء Omega V70 ◈◈")
        try:
            await self.c1.connect()
            if not await self.c1.is_user_authorized(): raise Exception("جلسة 1 خاطئة")
            logger.info("✅ حساب 1 متصل")
        except Exception as e: logger.error(f"فشل حساب 1: {e}"); return
        if self.c2:
            try:
                await self.c2.connect()
                if not await self.c2.is_user_authorized(): self.c2 = None
                else: logger.info("✅ حساب 2 متصل")
            except: self.c2 = None

        @self.c1.on(events.NewMessage)
        async def c1_handler(event):
            if event.sender_id == ADMIN_ID and event.raw_text.startswith("."):
                await self.execute_command(event, event.raw_text.split())
                return
            await self.process_message(event, self.c1, acc_num=1)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def c2_handler(event):
                await self.process_message(event, self.c2, acc_num=2)

        asyncio.create_task(self.keep_alive(self.c1, "Admin"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2, "Worker"))
        asyncio.create_task(self.persona_loop())

        # ماسح الهدايا كل 10 دقائق
        async def scanner_loop():
            while self.running:
                await asyncio.sleep(600)
                if self.sniper_active:
                    await self._scan_recent_gifts()
        asyncio.create_task(scanner_loop())

        logger.info("🚀 Omega V70 انطلق")
        await self.c1.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(OmegaV70().main())
    except KeyboardInterrupt: pass
