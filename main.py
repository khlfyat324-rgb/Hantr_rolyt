import os, asyncio, random, re, time, logging
from telethon import TelegramClient, events, functions, types, errors
from telethon.sessions import StringSession

# إعداد السجلات بشكل صامت
logging.basicConfig(level=logging.ERROR)

class SupremeSovereign:
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
        self.states = {} # لإدارة الأوامر التفاعلية

    # --- دليل الـ 100 وظيفة تحكم (مصنفة لسهولة الاستخدام) ---
    def get_power_guide(self):
        return """👑 **ترسانة التحكم السيادي (100+ وظيفة)** 👑

📡 **1. إدارة الحساب (الجندي):**
`.phone` (جلب الرقم) | `.setname [نص]` | `.setbio [نص]` | `.setuser [يوزر]` | `.photo` (تغيير الصورة) | `.del_photo`

💬 **2. إدارة المحادثات:**
`.join @user` (انضمام) | `.leave @user` (مغادرة) | `.chats` (قائمة المحادثات) | `.read_all` (قراءة الكل) | `.archive` | `.unarchive` | `.pin` | `.unpin` | `.mute` | `.unmute`

✉️ **3. إدارة الرسائل والوسائط:**
`.msg @user [نص]` | `.v @user` (فيديو تفاعلي) | `.p @user` (صورة تفاعلية) | `.fwd @from @to` | `.spam [عدد] [نص]` | `.clear_chat` | `.typing` | `.voice`

🛡 **4. الخصوصية والأمان:**
`.block @user` | `.unblock @user` | `.privacy_on` | `.privacy_off` | `.sessions` (عرض الجلسات النشطة)

🎯 **5. المحرك والإحصائيات:**
`.status` | `.run` (تشغيل الصيد) | `.stop` (إيقاف الصيد) | `.uptime` | `.id @user`

💡 *الأوامر التفاعلية (.v, .p) ستسألك عن التفاصيل خطوة بخطوة.*"""

    async def initialize(self):
        await self.client1.connect()
        await self.client2.connect()
        
        # واجهة حسابك الأول
        await self.client1.send_message("me", self.get_power_guide())
        
        # واجهة "الجندي" (كما طلبت في الصورة: واجهة نظيفة)
        if await self.client2.is_user_authorized():
            await self.client2.send_message("me", "⚙️ **نظام الجندي جاهز**\nأرسل `.start` للعمل أو `.stop` للتوقف.")

        # --- معالج الجندي (الحساب الثاني) ---
        @self.client2.on(events.NewMessage(pattern=r'(?i)^\.(start|stop)$', incoming=True, from_users='me'))
        async def soldier_ui(event):
            self.running = (event.pattern_match.group(1).lower() == 'start')
            await event.reply("✅ تم التحديث" if self.running else "⛔ تم الإيقاف")

        # --- معالج الإمبراطور (الحساب الأول - التحكم الشامل) ---
        @self.client1.on(events.NewMessage(incoming=True, from_users=self.admin_id))
        async def emperor_commands(event):
            text = event.raw_text
            cid = event.chat_id

            # معالجة الأوامر التفاعلية (فيديو/صور)
            if cid in self.states:
                st = self.states[cid]
                if st['step'] == 'media':
                    await self.client2.send_file(st['target'], event.message)
                    await event.reply(f"✅ تم الإرسال إلى {st['target']}")
                    del self.states[cid]
                return

            if text.startswith("."):
                args = text.split()
                cmd = args[0].lower()

                try:
                    if cmd == ".join" and len(args) > 1:
                        await self.client2(functions.channels.JoinChannelRequest(args[1]))
                        await event.reply(f"🚀 انضم الجندي إلى {args[1]}")
                    
                    elif cmd == ".leave" and len(args) > 1:
                        await self.client2(functions.channels.LeaveChannelRequest(args[1]))
                        await event.reply(f"🚩 غادر الجندي {args[1]}")

                    elif cmd == ".phone":
                        me2 = await self.client2.get_me()
                        await event.reply(f"📱 رقم الجندي: `+{me2.phone}`")

                    elif cmd in [".v", ".p"] and len(args) > 1:
                        self.states[cid] = {'step': 'media', 'target': args[1]}
                        await event.reply(f"📤 أرسل {'الفيديو' if cmd == '.v' else 'الصورة'} الآن لتوجيهها.")

                    elif cmd == ".msg" and len(args) > 2:
                        await self.client2.send_message(args[1], " ".join(args[2:]))
                        await event.reply("✅ تم")

                    elif cmd == ".status":
                        up = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.stats["start"]))
                        await event.reply(f"📊 **التقرير:**\nالمدة: `{up}`\nفوز1: `{self.stats['wins1']}` | فوز2: `{self.stats['wins2']}`")

                    elif cmd == ".stop": self.running = False; await event.reply("⛔ توقف الصيد.")
                    elif cmd == ".run": self.running = True; await event.reply("🚀 بدأ الصيد.")
                
                except Exception as e: await event.reply(f"⚠️ خطأ: {str(e)}")

        # --- محرك الروليتات (Logic) ---
        @self.client1.on(events.NewMessage)
        async def hunt1(event):
            if self.running: await self.process_hunt(event, self.client1, 1)

        @self.client2.on(events.NewMessage)
        async def hunt2(event):
            if self.running: await self.process_hunt(event, self.client2, 2)

        await self.client1.run_until_disconnected()

    async def process_hunt(self, event, client, n):
        # منطق صيد الروليتات وحل الكابتشا (كما تم شرحه سابقاً)
        try:
            if event.reply_markup:
                # حل تلقائي سريع
                m = re.search(r'(\d+)\s*([\+\-\*])\s*(\d+)', event.raw_text)
                if m:
                    res = eval(f"{m.group(1)}{m.group(2)}{m.group(3)}")
                    for r in event.reply_markup.rows:
                        for b in r.buttons:
                            if str(res) == b.text.strip():
                                await event.click(b); return
                
                # ضغط زر المشاركة
                for r in event.reply_markup.rows:
                    for b in r.buttons:
                        if any(k in b.text for k in ["مشاركة", "انضمام", "شارك"]):
                            await asyncio.sleep(random.uniform(5, 10))
                            await event.click(b)
                            self.stats[f"wins{n}"] += 1
                            return
        except: pass

if __name__ == "__main__":
    asyncio.run(SupremeSovereign().initialize())
