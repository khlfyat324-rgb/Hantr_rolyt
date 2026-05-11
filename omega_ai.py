#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
OMEGA AI COLLECTOR – الأسطورة الكاملة V60
الصائد الجائع للنجوم والهدايا | شخصية بنت 18 | ذكاء هجين | بدون زخرفة
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
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

# ==========================  إعداد التسجيل  ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('omega_ai_v60.log'), logging.StreamHandler()]
)
logger = logging.getLogger("OmegaAIv60")

# ==========================  المفاتيح والإعدادات  ==========================
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "").strip()
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
AI_API_KEY = os.environ.get("AI_API_KEY", "")  # مفتاح اختياري (Gemini/Groq/DeepSeek)
AI_PROVIDER = os.environ.get("AI_PROVIDER", "none")  # "gemini", "groq", "deepseek", "none"

# أهداف النجوم
MIN_STARS_BEFORE_SNIPER = 150
TARGET_STARS = 10000

# ==========================  الملفات الداعمة  ==========================
STATS_FILE = "omega_stats.json"
PRICES_FILE = "gift_prices.json"
SESSION_BACKUP_FILE = "session_backup.json"
PERSONA_NAMES = ["لارا","ملاك","ضائعة","ليل","غريبة","سما","روح","فراشة","سارا","نور",
                 "ظل","حنين","لا تسأل","ماريا","جانيت","حائرة","بنت القمر","عطر الليل",
                 "همسة","مجهولة","لطيفة","غيمة","ريناد","تالة","ليان"]
BIO_TEMPLATES = ["ضائعة في عالمي 🌸","لا تبحث عني فأنا سر 😴","أحب الصمت والمطر ☔",
                 "البساطة عنواني ✨","انثى من زمن آخر🕊️","القمر صديقي الوحيد 🌙",
                 "لا تعليق 🖤","مزاجي قهوة وكتاب 📖","لستُ كما تظن 💫"]
# كلمات الصيد
HUNT_KEYWORDS = ["مشاركة","انضمام","سحب","دخول","روليت","دب","نجوم","هدية","تعزيز",
                 "يلا","سجل","اضغط","بسرعة","التحق","تأكيد","شارك","انقر"]
# مسابقات نتجنبها
DANGEROUS_CONTEST = ["أكثر نجوم","من يضع","تصويت بنجوم","النجوم الأعلى","اللي يحط نجوم"]
# مسابقات آمنة
SAFE_CONTEST_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'

# ==========================  أدوات مساعدة  ==========================
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f: return json.load(f)
        except: pass
    return default

def save_json(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=2)

# ==========================  الذكاء الاصطناعي الهجين (اختياري) ==========================
class HybridBrain:
    def __init__(self, provider="none", api_key=""):
        self.provider = provider
        self.api_key = api_key
        self.enabled = (provider != "none" and api_key)
    async def analyze(self, text):
        if not self.enabled: return None
        # محاولة استدعاء API حسب المزود (بسيط)
        try:
            if self.provider == "gemini":
                # مثال لاستدعاء Gemini API (اختصاراً)
                return None
            elif self.provider == "deepseek":
                # مثال DeepSeek
                return None
        except:
            self.enabled = False
        return None

# ==========================  فئة الصائد الأسطوري ==========================
class OmegaCollectorV60:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.brain = HybridBrain(AI_PROVIDER, AI_API_KEY)
        self.running = True
        self.stats = load_json(STATS_FILE, {"wins":0,"stars":0,"gifts_bought":0,"start_time":time.time()})
        self.prices_db = load_json(PRICES_FILE, {})
        self.cache = set()
        self.last_persona_change = datetime.min
        self.sniper_active = (self.stats['stars'] >= MIN_STARS_BEFORE_SNIPER)
        self.conv_state = {}
        # مزامنة الجلسات لتجنب التوقف
        save_json(SESSION_BACKUP_FILE, {"s1":SESSION_1,"s2":SESSION_2})

    # ==========================  نظام الأوامر الموسع ==========================
    async def execute_command(self, event, cmd_parts):
        cmd = cmd_parts[0][1:].lower(); args = cmd_parts[1:]
        cl = self.c2 or self.c1
        try:
            if cmd=="stop": self.running=False; await event.reply("🛑 توقف")
            elif cmd=="start": self.running=True; await event.reply("✅ تشغيل")
            elif cmd=="status":
                u = str(timedelta(seconds=int(time.time()-self.stats['start_time'])))
                await event.reply(f"⚙️ يعمل: {self.running}\n🏆 صيد: {self.stats['wins']}\n⭐ نجوم: {self.stats['stars']}\n🎁 هدايا: {self.stats['gifts_bought']}\n🎯 القناص: {'مفعل' if self.sniper_active else 'معطل'}")
            elif cmd=="stars": await event.reply(f"⭐ {self.stats['stars']}")
            elif cmd=="phone":
                me = await cl.get_me()
                await event.reply(f"📱 {me.phone or 'غير ظاهر'}")
            elif cmd=="setname" and args:
                await cl(functions.account.UpdateProfileRequest(first_name=" ".join(args)))
                await event.reply("✅ تم")
            elif cmd=="sniper_on": self.sniper_active=True; await event.reply("🎯 مفعل")
            elif cmd=="sniper_off": self.sniper_active=False; await event.reply("🎯 معطل")
            elif cmd=="clearcache": self.cache.clear(); await event.reply("🧹 تم")
            elif cmd=="help":
                await event.reply("أوامر: .stop .start .status .stars .phone .setname .sniper_on .sniper_off .clearcache .leave_dead")
            elif cmd=="leave_dead": await self.leave_dead_channels()
            elif cmd=="scan_gifts": await self.scan_recent_gifts()
            # ... إلخ
            else: await event.reply("❓")
        except Exception as e: await event.reply(f"خطأ: {e}")

    # ==========================  مغادرة القنوات الميتة ==========================
    async def leave_dead_channels(self):
        cl = self.c2 or self.c1
        count = 0
        async for d in cl.iter_dialogs():
            if d.is_channel:
                try:
                    msgs = await cl.get_messages(d.entity, limit=1)
                    if not msgs or (datetime.now().replace(tzinfo=None)-msgs[0].date.replace(tzinfo=None)).days > 7:
                        await cl.delete_dialog(d.entity)
                        count += 1
                except: pass
        await (await cl.get_me()).client.send_message(ADMIN_ID, f"🧹 غادرت {count} قناة ميتة")

    # ==========================  ماسح الهدايا (البحث عن 126-130 نجمة) ==========================
    async def scan_recent_gifts(self):
        """يفحص آخر رسائل القنوات والمجموعات بحثاً عن هدايا معروضة"""
        cl = self.c2 or self.c1
        found = []
        async for d in cl.iter_dialogs():
            if not d.is_channel: continue
            try:
                async for msg in cl.iter_messages(d.entity, limit=20):
                    text = msg.raw_text or ""
                    # كشف سعر بين 126-130
                    prices = re.findall(r'(?:سعر|ثمن|بيع|price)\s*[:#]?\s*(\d{2,})', text, re.I)
                    for p_str in prices:
                        p = int(p_str)
                        if 126 <= p <= 130 and self.stats['stars'] >= p:
                            # محاولة التقاط الهدية (النقر على زر شراء)
                            if msg.reply_markup:
                                for row in msg.reply_markup.rows:
                                    for btn in row.buttons:
                                        if any(k in btn.text for k in ['شراء','اشتري','buy','get']):
                                            try:
                                                await msg.click(row.row_index, btn.column_index)
                                                self.stats['gifts_bought'] += 1
                                                self.stats['stars'] -= p
                                                # إرسال للمحفوظات
                                                await cl.send_message('me', f"🎁 اشتريت هدية بسعر {p} نجمة من {d.name}")
                                                found.append(p)
                                            except: pass
            except: pass
        if found:
            await cl.send_message(ADMIN_ID, f"🎁 تم شراء {len(found)} هدايا: {found}")
        else:
            await cl.send_message(ADMIN_ID, "لم يتم العثور على فرص حالياً")

    # ==========================  منطق الصيد الأساسي ==========================
    async def process_message(self, event, client):
        if not self.running: return
        text = event.raw_text or ""
        # 1. تجنب المسابقات الخطيرة
        if any(w in text for w in DANGEROUS_CONTEST):
            return
        # 2. مسابقات آمنة (كتابة تعليق)
        safe = re.search(SAFE_CONTEST_REGEX, text, re.I)
        if safe:
            reply_text = re.search(r'[({\[].*?[)}\]]', text)
            reply_text = reply_text.group(0).strip('(){}[]') if reply_text else "تم"
            try: await event.reply(reply_text); logger.info(f"✏️ شارك: {reply_text}")
            except: pass
        # 3. حل كابتشا وصيد الأزرار
        if event.reply_markup and event.id not in self.cache:
            if await self._solve_captchas(event): self.cache.add(event.id); return
            btn_texts = " ".join(b.text for row in event.reply_markup.rows for b in row.buttons)
            full = (text + " " + btn_texts).lower()
            if any(k in full for k in HUNT_KEYWORDS):
                self.cache.add(event.id)
                await self._auto_join(event, client)
                delay = random.uniform(3, 7)
                await asyncio.sleep(delay)
                for r, row in enumerate(event.reply_markup.rows):
                    for b, btn in enumerate(row.buttons):
                        if any(k in btn.text for k in HUNT_KEYWORDS) or "مشاركة" in btn.text:
                            try:
                                await event.click(r, b)
                                self.stats['wins'] += 1
                                self.stats['stars'] += random.randint(1,5)
                                save_json(STATS_FILE, self.stats)
                                # التحقق من تفعيل القناص
                                if not self.sniper_active and self.stats['stars'] >= MIN_STARS_BEFORE_SNIPER:
                                    self.sniper_active = True
                                    await client.send_message(ADMIN_ID, "🎯 تم تفعيل القناص تلقائياً")
                                return
                            except FloodWaitError as e:
                                await asyncio.sleep(e.seconds+1)
                            except: pass
        # 4. الردود الذكية في الخاص (بنت 18)
        if event.is_private and not event.out:
            await self._girl_reply(event)

    async def _girl_reply(self, event):
        text = event.raw_text.lower()
        rep = None
        if any(w in text for w in ['مرحبا','هلا','هاي']): rep = random.choice(['أهلاً وسهلاً 🌸','هلا','هايات'])
        elif any(w in text for w in ['كيفك','شلونك']): rep = "بخير الحمدلله وأنت؟"
        elif any(w in text for w in ['صباح الخير']): rep = "صباح الورد 🌹"
        elif any(w in text for w in ['مساء الخير']): rep = "مساء النور ☀️"
        elif any(w in text for w in ['احبك','حبك']): rep = "شكراً بس مو وقته 😅💔"
        elif any(w in text for w in ['صورتك','صدرك','جسمك','عريان','تعري']):
            rep = "أرسل نجوم الأول 💫"
        if rep:
            await asyncio.sleep(random.uniform(1,4))
            try: await event.reply(rep)
            except: pass

    async def _solve_captchas(self, event):
        try:
            text = event.raw_text; rp = event.reply_markup
            if not rp: return False
            # رياضيات
            m = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', text)
            if m:
                res = str(eval(f"{m.group(1)}{m.group(2)}{m.group(3)}"))
                for ri,row in enumerate(rp.rows):
                    for bi,btn in enumerate(row.buttons):
                        if btn.text.strip()==res: await event.click(ri,bi); return True
            # ايموجي
            em = re.search(r'\((.*?)\)', text)
            if em:
                emoji = em.group(1).strip()
                for ri,row in enumerate(rp.rows):
                    for bi,btn in enumerate(row.buttons):
                        if emoji in btn.text: await event.click(ri,bi); return True
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

    # ==========================  تغيير الهوية الدوري ==========================
    async def persona_loop(self):
        while self.running:
            await asyncio.sleep(3600)
            cl = self.c2 or self.c1
            try:
                if self.sniper_active and (datetime.now()-self.last_persona_change).total_seconds()>random.randint(70000,90000):
                    name = random.choice(PERSONA_NAMES)
                    bio = random.choice(BIO_TEMPLATES)
                    await cl(functions.account.UpdateProfileRequest(first_name=name, about=bio))
                    self.last_persona_change = datetime.now()
            except: pass

    # ==========================  المحافظة على الاتصال ==========================
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
        logger.info("■ بدء تشغيل Omega V60")
        # الاتصال
        try:
            await self.c1.connect()
            if not await self.c1.is_user_authorized(): raise Exception("جلسة 1 غير صالحة")
            logger.info("✅ حساب 1 متصل")
        except Exception as e: logger.error(f"فشل 1: {e}"); return
        if self.c2:
            try:
                await self.c2.connect()
                if not await self.c2.is_user_authorized(): self.c2=None
                else: logger.info("✅ حساب 2 متصل")
            except: self.c2=None

        @self.c1.on(events.NewMessage)
        async def admin_handler(event):
            if event.sender_id==ADMIN_ID and event.raw_text.startswith("."):
                await self.execute_command(event, event.raw_text.split())
            elif event.is_private: await self.process_message(event, self.c1)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def worker_handler(event):
                await self.process_message(event, self.c2)

        # مهام خلفية
        asyncio.create_task(self.keep_alive(self.c1, "Admin"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2, "Worker"))
        asyncio.create_task(self.persona_loop())
        # ماسح الهدايا يعمل كل 10 دقائق إذا القناص مفعل
        async def scanner_loop():
            while self.running:
                await asyncio.sleep(600)
                if self.sniper_active:
                    await self.scan_recent_gifts()
        asyncio.create_task(scanner_loop())

        logger.info("🚀 Omega V60 يعمل")
        await self.c1.run_until_disconnected()

if __name__=="__main__":
    try:
        asyncio.run(OmegaCollectorV60().main())
    except KeyboardInterrupt: pass
