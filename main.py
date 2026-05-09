import os, asyncio, random, re, time, logging
from telethon import TelegramClient, events, functions, types, errors
from telethon.sessions import StringSession

# إعداد السجلات بشكل صامت واحترافي
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("Sovereign_V70")

class SovereignEmpire:
    def __init__(self):
        # استدعاء البيانات من البيئة الآمنة (GitHub Secrets)
        self.api_id_1 = int(os.environ.get("API_ID_1", 0))
        self.api_hash_1 = os.environ.get("API_HASH_1", "")
        self.session_1 = os.environ.get("SESSION_1", "").strip()
        self.admin_id = int(os.environ.get("ADMIN_ID", 0))
        
        self.api_id_2 = int(os.environ.get("API_ID_2", 0))
        self.api_hash_2 = os.environ.get("API_HASH_2", "")
        self.session_2 = os.environ.get("SESSION_2", "").strip()
        
        self.client1 = TelegramClient(StringSession(self.session_1), self.api_id_1, self.api_hash_1)
        self.client2 = TelegramClient(StringSession(self.session_2), self.api_id_2, self.api_hash_2)
        
        self.running = True
        self.stats = {"wins1": 0, "wins2": 0, "start": time.time()}
        self.keywords = ["مشاركة", "انضمام", "سحب", "دخول", "الاشتراك", "روليت", "نجوم", "هنا", "اضغط"]
        self.states = {}

    # --- قائمة الأوامر الشاملة والمبسطة ---
    def help_menu(self):
        return """👑 **لوحة تحكم الإمبراطور (حسابك الأول)** 👑

📡 **أوامر التحكم بالجندي (الحساب الثاني):**
• `.join @user` : انضمام الجندي لقناة/مجموعة.
• `.leave @user`: مغادرة الجندي لقناة/مجموعة.
• `.phone` : جلب رقم هاتف الجندي (حتى لو مخفي).
• `.msg @user [نص]` : إرسال رسالة من الجندي.
• `.v @user` : إرسال فيديو تفاعلي (يطلب منك اليوزر ثم الفيديو).
• `.chats` : عرض آخر 20 محادثة للجندي.
• `.block @user` | `.unblock @user` : التحكم بالحظر.
• `.setname [اسم]` | `.setbio [بايو]` : تغيير البيانات.

🎯 **أوامر المحرك العام:**
• `.status` : عرض الإحصائيات والفوز.
• `.stop` : إيقاف الصيد في الحسابين.
• `.run` : تشغيل الصيد في الحسابين.

💡 *أي أمر آخر تريده، الحساب مهيأ لتنفيذه برمجياً.*"""

    async def start_engine(self):
        # تشغيل العملاء (بدون طلب مدخلات)
        await self.client1.connect()
        await self.client2.connect()

        if not await self.client1.is_user_authorized(): return
        
        # إرسال الدليل لحسابك الأول (الرسائل المحفوظة)
        await self.client1.send_message("me", self.help_menu())
        
        # إرسال start/stop فقط لحساب الجندي (الرسائل المحفوظة)
        if await self.client2.is_user_authorized():
            await self.client2.send_message("me", "🎮 **لوحة تشغيل الجندي:**\nأرسل `start` للعمل أو `stop` للتوقف.")

        # --- معالج الحساب الجندي (Saved Messages فقط) ---
        @self.client2.on(events.NewMessage(pattern=r'(?i)^(start|stop)$', incoming=True, from_users='me'))
        async def soldier_self_control(event):
            if event.raw_text.lower() == 'stop':
                self.running = False
                await event.reply("⛔ تم الإيقاف.")
            else:
                self.running = True
                await event.reply("🚀 تم التشغيل.")

        # --- معالج الحساب الأول (الأوامر السيادية) ---
        @self.client1.on(events.NewMessage(incoming=True, from_users=self.admin_id))
        async def primary_control(event):
            text = event.raw_text
            chat_id = event.chat_id

            # نظام الأوامر التفاعلية (مثل الفيديو)
            if chat_id in self.states:
                st = self.states[chat_id]
                if st['step'] == 'video' and event.video:
                    await self.client2.send_file(st['target'], event.video)
                    await event.reply("✅ تم إرسال الفيديو من الجندي.")
                    del self.states[chat_id]
                return

            if text.startswith("."):
                args = text.split()
                cmd = args[0]

                try:
                    if cmd == ".join" and len(args) > 1:
                        await self.client2(functions.channels.JoinChannelRequest(args[1]))
                        await event.reply(f"✅ الجندي انضم إلى {args[1]}")
                    
                    elif cmd == ".leave" and len(args) > 1:
                        await self.client2(functions.channels.LeaveChannelRequest(args[1]))
                        await event.reply(f"✅ الجندي غادر {args[1]}")

                    elif cmd == ".phone":
                        me2 = await self.client2.get_me()
                        await event.reply(f"📱 رقم الجندي: `+{me2.phone}`")

                    elif cmd == ".msg" and len(args) > 2:
                        await self.client2.send_message(args[1], " ".join(args[2:]))
                        await event.reply("✅ تم الإرسال.")

                    elif cmd == ".v" and len(args) > 1:
                        self.states[chat_id] = {'step': 'video', 'target': args[1]}
                        await event.reply(f"🎬 أرسل الفيديو الآن ليتم توجيهه إلى {args[1]}")

                    elif cmd == ".chats":
                        dialogs = await self.client2.get_dialogs(limit=20)
                        msg = "💬 **محادثات الجندي:**\n" + "\n".join([f"- {d.name} (@{d.entity.username if getattr(d.entity, 'username', None) else d.id})" for d in dialogs])
                        await event.reply(msg)

                    elif cmd == ".status":
                        up = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.stats["start"]))
                        await event.reply(f"📊 **التقرير:**\nالمدة: `{up}`\nفوز1: `{self.stats['wins1']}` | فوز2: `{self.stats['wins2']}`")

                    elif cmd == ".stop": self.running = False; await event.reply("⛔ توقف المحرك.")
                    elif cmd == ".run": self.running = True; await event.reply("🚀 انطلق المحرك.")
                
                except Exception as e:
                    await event.reply(f"❌ خطأ: {str(e)}")

        # --- محرك الروليتات الموحد ---
        @self.client1.on(events.NewMessage)
        async def hunt1(event):
            if self.running: await self.logic(event, self.client1, 1)

        @self.client2.on(events.NewMessage)
        async def hunt2(event):
            if self.running: await self.logic(event, self.client2, 2)

        await self.client1.run_until_disconnected()

    async def logic(self, event, client, n):
        try:
            # حل الكابتشا (رياضيات + تصويت)
            if event.reply_markup:
                m = re.search(r'(\d+)\s*([\+\-\*])\s*(\d+)', event.raw_text)
                if m:
                    res = eval(f"{m.group(1)}{m.group(2)}{m.group(3)}")
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if str(res) == btn.text.strip():
                                await event.click(r_idx, b_idx)
                                return

                v = re.search(r'\((.*?)\)', event.raw_text)
                if v:
                    emoji = v.group(1).strip()
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if emoji in btn.text:
                                await event.click(r_idx, b_idx)
                                return

            # الانضمام للروليت
            if any(k in event.raw_text.lower() for k in self.keywords) or (event.reply_markup and "مشاركة" in str(event.reply_markup)):
                # كشف السرعة
                delay = random.uniform(4, 6) if "المشارك" in event.raw_text else random.uniform(10, 15)
                await asyncio.sleep(delay)
                
                if event.reply_markup:
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if any(k in btn.text for k in ["مشاركة", "انضمام", "تأكيد"]):
                                await event.click(r_idx, b_idx)
                                self.stats[f"wins{n}"] += 1
                                return
        except: pass

if __name__ == "__main__":
    sov = SovereignEmpire()
    asyncio.run(sov.start_engine())
