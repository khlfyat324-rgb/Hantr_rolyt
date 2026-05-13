#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
Omega Final Legend – الصاروخ الأسطوري
- أمر .giftlog لعرض مشتريات الهدايا المطورة
- مغادرة القنوات الميتة كل 4 ساعات (يوم صمت فقط)
- ردود بشرية فائقة الذكاء (لا تُرسل إلا لرسائل النجوم القصيرة)
- تحويل الهدايا تلقائياً، صيد الروليتات، قناص الهدايا
- لوحة تحكم تفاعلية
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""
import os, sys, asyncio, random, re, time, json, logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types, Button
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateStatusRequest, UpdateProfileRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.errors import AuthKeyDuplicatedError, FloodWaitError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('legend.log'), logging.StreamHandler()])
logger = logging.getLogger("Legend")

# ---------- الإعدادات ----------
API_ID_1 = int(os.environ.get("API_ID_1", 0))
API_HASH_1 = os.environ.get("API_HASH_1", "")
SESSION_1 = os.environ.get("SESSION_1", "").strip()
API_ID_2 = int(os.environ.get("API_ID_2", 0))
API_HASH_2 = os.environ.get("API_HASH_2", "")
SESSION_2 = os.environ.get("SESSION_2", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

SNIPER_MIN = 100
SNIPER_MAX = 130
DEAD_CHANNEL_DAYS = 1          # أغادر بعد يوم واحد من الصمت
PERSONA_NAMES = ["لارا","ملاك","ضائعة","ليل","غريبة","سما","روح","فراشة","سارا","نور","ظل","حنين","لا تسأل","ماريا"]
PERSONA_BIOS = ["ضائعة في عالمي 🌸","لا تبحث عني فأنا سر 😴","أحب الصمت والمطر ☔","البساطة عنواني ✨"]
HUNT_WORDS = ["مشاركة","انضمام","سحب","دخول","روليت","دب","هدية","نجوم","تعزيز","يلا","سجل","اضغط","بسرعة","التحق","تأكيد","شارك","انقر"]
DANGER_WORDS = ["أكثر نجوم","من يضع","تصويت بنجوم","اكثر شخص يحط","يحط يربح","مزاد نجوم"]
SAFE_REGEX = r'أول\s*(شخص|واحد|من)\s*(ي|يلي)?\s*(كتب|يكتب|قال|يقول|رد|يرد|علق|يعلق)\s*[({\[].*?[)}\]]'
STAR_EMOJIS = ['⭐','🌟','✨','💫','⭐️','❤️','💙','💜','🧡','💛','💚','🤍','🤎','🩷','🩵','💖','💝','💘','💗','💓','💞','💕','🎁','🍭','🚀','🐱']

class Legend:
    def __init__(self):
        self.c1 = TelegramClient(StringSession(SESSION_1), API_ID_1, API_HASH_1)
        self.c2 = TelegramClient(StringSession(SESSION_2), API_ID_2, API_HASH_2) if SESSION_2 else None
        self.running = True
        self.stars = 0
        self.sniper = False
        self.persona_time = datetime.min
        self.cache = set()
        self.gift_log = []          # قائمة لتخزين الهدايا المشتراة
        self.stats = {"wins":0,"stars_earned":0,"gifts_bought":0,"gifts_converted":0,"channels_left":0,"start":time.time()}

    # ====================== اتصال حديدي ======================
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

    async def keep_alive(self, client, name):
        while self.running:
            try:
                if not client.is_connected(): await self.iron_connect(client, name)
                await client(UpdateStatusRequest(offline=False))
                await client(functions.PingRequest(ping_id=random.randint(0,2**31)))
            except AuthKeyDuplicatedError:
                await client.disconnect()
                await asyncio.sleep(60)
            except: pass
            await asyncio.sleep(120)

    # ====================== هدايا واردة وتحويلها ======================
    async def convert_gift(self, event, client):
        if not event.reply_markup: return False
        if any(w in (event.raw_text or "") for w in ['هدية من','أضاف','الهدية','إلى ملفك']):
            for row in event.reply_markup.rows:
                for btn in row.buttons:
                    if any(k in btn.text for k in ['تحويل','نجمة','convert','stars','عرض']):
                        await event.click(row.row_index, btn.column_index)
                        self.stats['gifts_converted'] += 1
                        self.stars += random.randint(10,50)
                        await self.log(client, f"🎁 تم تحويل هدية")
                        return True
        return False

    # ====================== قناص الهدايا ======================
    async def snipe(self, event, client):
        if not self.sniper or not event.reply_markup: return
        text = event.raw_text or ""
        prices = re.findall(r'(?:سعر|ثمن|بيع|price)\s*[:#]?\s*(\d{2,})', text, re.I)
        for p_str in prices:
            price = int(p_str)
            if SNIPER_MIN <= price <= SNIPER_MAX and self.stars >= price:
                gift = "هدية"
                m = re.search(r'(?:هدية|Gift)\s*["\']?([\w\s]+)', text, re.I)
                if m: gift = m.group(1).strip()
                for row in event.reply_markup.rows:
                    for btn in row.buttons:
                        if any(k in btn.text for k in ['شراء','اشتري','buy','get']):
                            await event.click(row.row_index, btn.column_index)
                            self.stats['gifts_bought'] += 1
                            self.stars -= price
                            chat = await event.get_chat()
                            src = chat.title if hasattr(chat,'title') else "خاص"
                            self.gift_log.append((gift, price, src, datetime.now().strftime("%H:%M")))
                            await self.log(client, f"💎 اشترى {gift} بـ{price} نجمة من {src}")
                            return True

    # ====================== مغادرة القنوات الميتة بقوة ======================
    async def leave_dead(self, client):
        count = 0
        async for d in client.iter_dialogs():
            if not d.is_channel: continue
            try:
                msgs = await client.get_messages(d.entity, limit=1)
                if not msgs or not msgs[0].date: 
                    await client(LeaveChannelRequest(d.entity)); count+=1; continue
                delta = datetime.now(tz=None) - msgs[0].date.replace(tzinfo=None)
                if delta.days > DEAD_CHANNEL_DAYS:
                    txt = msgs[0].raw_text or ""
                    if not any(k in txt for k in HUNT_WORDS+['مسابقة','روليت','سحب']):
                        await client(LeaveChannelRequest(d.entity))
                        count += 1
            except: pass
        self.stats['channels_left'] += count
        if count: await self.log(client, f"🧹 غادرت {count} قناة صامتة")

    # ====================== ردود بشرية ذكية جداً ======================
    async def human_reply(self, event, client):
        if event.out or not event.is_private: return False
        text = event.raw_text or ""
        if len(text) > 50 or not any(e in text for e in STAR_EMOJIS): return False
        await asyncio.sleep(random.uniform(5,20))
        try: await client(functions.messages.ReadHistoryRequest(peer=event.chat_id, max_id=event.id))
        except: pass
        await asyncio.sleep(random.uniform(1,3))
        async with client.action(event.chat_id, 'typing'):
            await asyncio.sleep(random.uniform(1.5,3))
        rep = random.choice(["شكراً 💫","تسلم 🌸","الله يسعدك 💝","ما تقصر ✨","💖","🌸"])
        try: await event.reply(rep); return True
        except: pass

    # ====================== معالجة الرسالة ======================
    async def process(self, event, client):
        if not self.running: return
        text = event.raw_text or ""
        if await self.convert_gift(event, client): return
        if any(w in text for w in DANGER_WORDS): return
        safe = re.search(SAFE_REGEX, text, re.I)
        if safe:
            m = re.search(r'[({\[].*?[)}\]]', text)
            reply = m.group(0).strip('(){}[]') if m else "تم"
            try: await event.reply(reply)
            except: pass
            if event.reply_markup: await self._click_hunt(event, client)
            return
        if event.reply_markup and event.id not in self.cache:
            if any(k in (text+"".join(b.text for r in event.reply_markup.rows for b in r.buttons)).lower() for k in HUNT_WORDS):
                self.cache.add(event.id)
                await self._auto_join(event, client)
                await asyncio.sleep(random.uniform(2,6))
                await self._click_hunt(event, client)
        await self.snipe(event, client)
        await self.human_reply(event, client)

    async def _click_hunt(self, event, client):
        for r,row in enumerate(event.reply_markup.rows):
            for b,btn in enumerate(row.buttons):
                if any(k in btn.text for k in HUNT_WORDS) or "مشاركة" in btn.text:
                    try:
                        await event.click(r,b)
                        self.stats['wins']+=1
                        self.stars+=random.randint(1,5)
                        if not self.sniper and self.stars>=100: 
                            self.sniper=True
                            await self.log(client, "🎯 تم تفعيل القناص")
                        await self.log(client, f"🏆 صيد! الرصيد ~{self.stars}")
                        return
                    except FloodWaitError as e: await asyncio.sleep(e.seconds+1)
                    except: pass

    async def _auto_join(self, event, client):
        links = set()
        if event.entities:
            for e in event.entities:
                if hasattr(e,'url') and 't.me' in (e.url or ''): links.add(e.url)
        links.update(re.findall(r't\.me/[\w\d_]+|@[\w\d_]+', event.raw_text))
        for l in links:
            name = l.split('/')[-1].replace('@','')
            try: await client(JoinChannelRequest(name))
            except: pass

    async def log(self, client, msg):
        try: await client.send_message('me', msg)
        except: pass

    # ====================== الأوامر ولوحة التحكم ======================
    async def command(self, event, parts, client):
        cmd = parts[0][1:].lower()
        args = parts[1:]
        if cmd=="panel":
            txt = "🔥 **الأسطورة – لوحة التحكم**\nانقر لنسخ الأمر:"
            btns = [
                [Button.inline(".status", b"copy_.status"), Button.inline(".stop", b"copy_.stop"), Button.inline(".start", b"copy_.start")],
                [Button.inline(".giftlog", b"copy_.giftlog"), Button.inline(".leavedead", b"copy_.leavedead")],
                [Button.inline(".sniper_on", b"copy_.sniper_on"), Button.inline(".sniper_off", b"copy_.sniper_off")],
                [Button.inline(".clearcache", b"copy_.clearcache"), Button.inline(".always_online", b"copy_.always_online")],
                [Button.inline(".setname اسم", b"copy_.setname"), Button.inline(".setbio نبذة", b"copy_.setbio")]
            ]
            await event.respond(txt, buttons=btns)
        elif cmd=="giftlog":
            if not self.gift_log:
                await event.reply("📭 لا توجد هدايا مشتراة بعد")
            else:
                msg = "**🎁 آخر 10 هدايا تم اصطيادها:**\n"
                for g,p,src,t in self.gift_log[-10:]:
                    msg += f"▫️ {g} – {p}⭐ | {src} | {t}\n"
                await event.reply(msg)
        elif cmd=="status":
            up = str(timedelta(seconds=int(time.time()-self.stats['start'])))
            await event.reply(f"⚙️ {'🟢' if self.running else '🔴'} | ⏱️{up}\n🏆{self.stats['wins']} | ⭐~{self.stars}\n🎁محولة:{self.stats['gifts_converted']} | 💎مشتراة:{self.stats['gifts_bought']}\n🚪غادرت:{self.stats['channels_left']} | 🎯القناص:{'مفعل' if self.sniper else 'معطل'}")
        elif cmd=="stop": self.running=False; await event.reply("🛑 توقف")
        elif cmd=="start": self.running=True; await event.reply("✅ تشغيل")
        elif cmd=="sniper_on": self.sniper=True; await event.reply("🎯 مفعل")
        elif cmd=="sniper_off": self.sniper=False; await event.reply("🎯 معطل")
        elif cmd=="leavedead":
            await self.leave_dead(client)
            await event.reply("🧹 جاري المغادرة...")
        elif cmd=="always_online":
            await client(UpdateStatusRequest(offline=False))
            await event.reply("🟢 متصل دائماً")
        elif cmd=="clearcache":
            self.cache.clear(); await event.reply("🗑️ تم")
        elif cmd=="setname" and args:
            await client(UpdateProfileRequest(first_name=" ".join(args)))
            await event.reply("✅ تم")
        elif cmd=="setbio" and args:
            await client(UpdateProfileRequest(about=" ".join(args)))
            await event.reply("✅ تم")
        elif cmd=="setphoto" and event.is_reply:
            r=await event.get_reply_message()
            if r.photo:
                up=await client.upload_file(r.photo)
                await client(functions.photos.UploadProfilePhotoRequest(file=up))
                await event.reply("🖼️ تم")
        else: await event.reply("❓")

    # ====================== الشخصية ======================
    async def persona_loop(self, client):
        while self.running:
            await asyncio.sleep(3600)
            if self.sniper and (datetime.now()-self.persona_time).total_seconds()>random.randint(70000,100000):
                await client(UpdateProfileRequest(first_name=random.choice(PERSONA_NAMES), about=random.choice(PERSONA_BIOS)))
                self.persona_time=datetime.now()

    # ====================== البداية ======================
    async def main(self):
        if not await self.iron_connect(self.c1,"ح1"): return
        self.main = self.c1
        if self.c2 and await self.iron_connect(self.c2,"ح2"): self.main = self.c2
        client = self.main

        @self.c1.on(events.NewMessage)
        async def h1(e):
            if e.sender_id==ADMIN_ID and e.raw_text.startswith("."): await self.command(e, e.raw_text.split(), self.c1)
            else: await self.process(e, self.c1)

        if self.c2:
            @self.c2.on(events.NewMessage)
            async def h2(e): await self.process(e, self.c2)

        @self.c1.on(events.CallbackQuery)
        async def cb1(e):
            if e.data.decode().startswith("copy_"): await e.answer("✅ تم النسخ", alert=False)

        asyncio.create_task(self.keep_alive(self.c1,"ح1"))
        if self.c2: asyncio.create_task(self.keep_alive(self.c2,"ح2"))
        asyncio.create_task(self.persona_loop(client))

        async def dead_loop():
            while self.running:
                await asyncio.sleep(14400)  # كل 4 ساعات
                await self.leave_dead(client)
        asyncio.create_task(dead_loop())

        await client(UpdateStatusRequest(offline=False))
        logger.info("🚀 الأسطورة تعمل")
        await self.c1.run_until_disconnected()

if __name__=="__main__":
    asyncio.run(Legend().main())
