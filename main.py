import os, asyncio, random, re, time, logging
from telethon import TelegramClient, events, functions, types, errors
from telethon.sessions import StringSession

# إعداد السجلات
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("Sovereign_V60")

class AbsoluteSovereign:
    def __init__(self):
        # تحميل البيانات من الأسرار
        self.api_id_1 = int(os.environ.get("API_ID_1", 0))
        self.api_hash_1 = os.environ.get("API_HASH_1", "")
        self.session_1 = os.environ.get("SESSION_1", "").strip()
        self.admin_id = int(os.environ.get("ADMIN_ID", 0))
        
        self.api_id_2 = int(os.environ.get("API_ID_2", 0))
        self.api_hash_2 = os.environ.get("API_HASH_2", "")
        self.session_2 = os.environ.get("SESSION_2", "").strip()
        
        # العملاء
        self.client1 = TelegramClient(StringSession(self.session_1), self.api_id_1, self.api_hash_1)
        self.client2 = TelegramClient(StringSession(self.session_2), self.api_id_2, self.api_hash_2)
        
        # متغيرات الحالة والتحكم
        self.states = {} # لتخزين مراحل الأوامر التفاعلية
        self.config = {"running": True, "trust": True}
        self.stats = {"wins1": 0, "wins2": 0, "start": time.time()}
        self.keywords = ["مشاركة", "انضمام", "سحب", "دخول", "الاشتراك", "روليت", "نجوم", "هنا", "اضغط"]

    # --- قائمة الأوامر المبسطة (شرح الـ 100 أمر) ---
    def get_simplified_help(self):
        return (
            "👑 **دليل التحكم السيادي V60** 👑\n\n"
            "🛡 **أوامر الحساب الثاني (الجندي):**\n"
            "• `.get_phone` : إظهار رقم هاتف الحساب الثاني فوراً.\n"
            "• `.send_video` : إرسال فيديو (سيقوم السكريبت بسؤالك عن التفاصيل).\n"
            "• `.list_chats` : رؤية آخر الأشخاص الذين تحدث معهم الحساب.\n"
            "• `.acc2_info` : فحص الحالة الكاملة للحساب (القيود، النجوم، الاسم).\n"
            "• `.acc2_msg` : إرسال رسالة نصية سريعة.\n\n"
            "⚙️ **أوامر المحرك (الروليتات):**\n"
            "• `.stop` : إيقاف الحسابين عن دخول الروليتات.\n"
            "• `.start` : إعادة تشغيل محرك الصيد.\n"
            "• `.status` : تقرير الأرباح والفوز الحالي.\n\n"
            "📝 **ملاحظة:** الأوامر التفاعلية (مثل إرسال فيديو) ستوجهك خطوة بخطوة. فقط أرسل الأمر واتبع التعليمات."
        )

    async def run(self):
        # تشغيل الحسابات بدون طلب مدخلات (تجنب EOFError)
        try:
            await self.client1.connect()
            if not await self.client1.is_user_authorized(): return
            await self.client1.send_message("me", "✅ **المحرك يعمل!**\nأرسل `.start` للبدء أو `.stop` للتوقف.\n\n" + self.get_simplified_help())
        except: pass

        try:
            await self.client2.connect()
        except: pass

        # --- معالج الأوامر التفاعلية والتحكم الشامل ---
        @self.client1.on(events.NewMessage(incoming=True, from_users=self.admin_id))
        async def admin_manager(event):
            msg = event.raw_text
            chat_id = event.chat_id

            # نظام الحالة (للمحادثات التفاعلية)
            if chat_id in self.states:
                state = self.states[chat_id]
                
                if state['cmd'] == 'send_video':
                    if 'target' not in state:
                        state['target'] = msg
                        await event.reply(f"🎯 تم تحديد الهدف: `{msg}`\nالآن أرسل لي (الفيديو) الذي تريد إرساله.")
                    elif event.video:
                        await self.client2.send_file(state['target'], event.video)
                        await event.reply("✅ تم إرسال الفيديو بنجاح من الحساب الثاني!")
                        del self.states[chat_id]
                return

            # الأوامر المباشرة
            if msg == ".get_phone":
                me2 = await self.client2.get_me()
                await event.reply(f"📱 رقم هاتف الحساب الثاني هو: `+{me2.phone}`")
            
            elif msg == ".send_video":
                self.states[chat_id] = {'cmd': 'send_video'}
                await event.reply("🎬 حسناً، أرسل لي (يوزر) الشخص الذي تريد إرسال الفيديو له.")

            elif msg == ".list_chats":
                dialogs = await self.client2.get_dialogs(limit=10)
                res = "💬 **آخر 10 محادثات في الحساب الثاني:**\n"
                for d in dialogs:
                    res += f"- {d.name} (ID: `{d.id}`)\n"
                await event.reply(res)

            elif msg == ".stop":
                self.config["running"] = False
                await event.reply("⛔ تم إيقاف محرك الصيد في الحسابين.")

            elif msg == ".start":
                self.config["running"] = True
                await event.reply("🚀 تم تشغيل محرك الصيد. الحسابان يبحثان الآن...")

            elif msg == ".status":
                up = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.stats["start"]))
                await event.reply(f"📊 **التقرير السيادي:**\n⏱ تشغيل منذ: `{up}`\n✅ فوز 1: `{self.stats['wins1']}`\n✅ فوز 2: `{self.stats['wins2']}`")

        # --- محرك الصيد المزدوج (Logic) ---
        @self.client1.on(events.NewMessage)
        async def hunter1(event):
            if self.config["running"]: await self.hunt_logic(event, self.client1, 1)

        @self.client2.on(events.NewMessage)
        async def hunter2(event):
            if self.config["running"]: await self.hunt_logic(event, self.client2, 2)

        await self.client1.run_until_disconnected()

    async def hunt_logic(self, event, client, num):
        try:
            # حل الكابتشا (رياضيات وتصويت)
            if event.reply_markup:
                # منطق الرياضيات
                m = re.search(r'(\d+)\s*([\+\-\*])\s*(\d+)', event.raw_text)
                if m:
                    res = eval(f"{m.group(1)}{m.group(2)}{m.group(3)}")
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if str(res) == btn.text.strip():
                                await event.click(r_idx, b_idx)
                                return

                # منطق التصويت (إيموجي بين قوسين)
                v = re.search(r'\((.*?)\)', event.raw_text)
                if v:
                    emoji = v.group(1).strip()
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if emoji in btn.text:
                                await event.click(r_idx, b_idx)
                                return

            # الانضمام للروليتات
            if any(k in event.raw_text.lower() for k in self.keywords) or (event.reply_markup and "مشاركة" in str(event.reply_markup)):
                is_fast = "المشارك" in event.raw_text
                await asyncio.sleep(random.uniform(5, 7) if is_fast else random.uniform(12, 18))
                
                # الضغط على زر المشاركة
                if event.reply_markup:
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if "مشاركة" in btn.text or "انضمام" in btn.text:
                                await event.click(r_idx, b_idx)
                                self.stats[f"wins{num}"] += 1
                                return
        except: pass

if __name__ == "__main__":
    sov = AbsoluteSovereign()
    asyncio.run(sov.run())
