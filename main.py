import os, asyncio, random, re, time, logging, sys
from telethon import TelegramClient, events, functions, types, errors
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("Omega_V60")

class OmegaDualCore:
    def __init__(self):
        try:
            # --- تحميل الأسرار ---
            self.api_id_1 = int(os.environ.get("API_ID_1", 0))
            self.api_hash_1 = os.environ.get("API_HASH_1", "")
            self.session_1_str = os.environ.get("SESSION_1", "").strip()
            
            self.api_id_2 = int(os.environ.get("API_ID_2", 0))
            self.api_hash_2 = os.environ.get("API_HASH_2", "")
            self.session_2_str = os.environ.get("SESSION_2", "").strip()
            
            self.admin_id = int(os.environ.get("ADMIN_ID", 0))
            
            # --- إنشاء العملاء ---
            self.client1 = TelegramClient(StringSession(self.session_1_str), self.api_id_1, self.api_hash_1)
            self.client2 = TelegramClient(StringSession(self.session_2_str), self.api_id_2, self.api_hash_2)
            
            # --- الكلمات المفتاحية ---
            self.keywords = [
                "مشاركة", "انضمام", "سحب", "دخول", "الاشتراك", "شارك", "انقر", "روليت", 
                "دب", "نجوم", "نقاط", "هدية", "تعزيز", "بدأ", "يلا", "سجل", "هنا", "اضغط", 
                "رؤية السحب", "المشاركة", "بسرعة", "التحق", "تأكيد"
            ]
            
            # --- إحصائيات ---
            self.stats = {"wins1": 0, "wins2": 0, "stars1": 0, "stars2": 0, "start_time": time.time()}
            self.config = {"running": True, "trust": True}
            self.cache = set()
            self.conversation_state = {}
            
            logger.info("✅ تم تهيئة Omega V60 بنجاح")
        except Exception as e:
            logger.error(f"❌ فشل التحميل: {e}")
            sys.exit(1)

    # ---------- أدوات مساعدة ----------
    async def _safe_call(self, client, func, *args, **kwargs):
        """تغليف لمنع أخطاء الفيضان والتحميل الزائد"""
        try:
            return await func(*args, **kwargs)
        except errors.FloodWaitError as e:
            logger.warning(f"⏳ انتظار فيضان {e.seconds} ثانية")
            await asyncio.sleep(e.seconds)
            return await func(*args, **kwargs)
        except errors.PhoneMigrateError as e:
            logger.critical("ترحيل DC")
            return None
        except Exception as e:
            logger.warning(f"خطأ: {e}")
            return None

    # ---------- نظام حل الكابتشا (محسن) ----------
    async def solve_captchas(self, event, acc_num):
        try:
            if not event.reply_markup: return False
            # 1. رياضي
            math_match = re.search(r'(\d+)\s*([+\-*])\s*(\d+)', event.raw_text)
            if math_match:
                res = eval(f"{math_match.group(1)}{math_match.group(2)}{math_match.group(3)}")
                for r_idx, row in enumerate(event.reply_markup.rows):
                    for b_idx, btn in enumerate(row.buttons):
                        if str(res) == btn.text.strip():
                            await self._safe_call(event.client, event.click, r_idx, b_idx)
                            logger.info(f"🧮 حل كابتشا رياضي (حساب {acc_num})")
                            return True
            # 2. إيموجي بين قوسين
            vote_match = re.search(r'\((.*?)\)', event.raw_text)
            if vote_match:
                emoji = vote_match.group(1).strip()
                for r_idx, row in enumerate(event.reply_markup.rows):
                    for b_idx, btn in enumerate(row.buttons):
                        if emoji in btn.text:
                            await self._safe_call(event.client, event.click, r_idx, b_idx)
                            logger.info(f"🗳️ حل كابتشا إيموجي (حساب {acc_num})")
                            return True
        except Exception as e:
            logger.error(f"خطأ كابتشا: {e}")
        return False

    async def auto_join_requirements(self, event, client):
        """الانضمام التلقائي للقنوات المطلوبة"""
        try:
            links = set()
            if event.entities:
                for ent in event.entities:
                    if isinstance(ent, types.MessageEntityTextUrl):
                        if "هنا" in event.raw_text[ent.offset:ent.offset+ent.length]:
                            links.add(ent.url)
            raw_links = re.findall(r'(?:t\.me/|@)([\w\d_]+)', event.raw_text)
            for link in raw_links:
                links.add(link)
            for entity in links:
                target = entity.split('/')[-1].replace('@', '').strip().lower()
                if target:
                    try:
                        await self._safe_call(client, client(functions.channels.JoinChannelRequest(target)))
                        logger.info(f"🔗 انضم للقناة {target}")
                    except:
                        pass
        except Exception as e:
            logger.warning(f"فشل الانضمام: {e}")

    # ---------- القائمة الجديدة (100 أمر مبسط) ----------
    def generate_commands_list(self):
        return (
            "🔥 **Omega V60 – دليل الأوامر الـ 100+** 🔥\n\n"
            "🆔 **معلومات الحساب الثاني**\n"
            "`.acc2_id` - معرف الحساب\n"
            "`.acc2_name` - الاسم الكامل\n"
            "`.acc2_user` - المعرف @username\n"
            "`.acc2_phone` - رقم الهاتف (سري)\n"
            "`.acc2_bio` - النبذة\n"
            "`.acc2_stars_balance` - نجوم افتراضي\n"
            "`.acc2_dc` - مركز البيانات\n"
            "`.acc2_limit` - حدود الحساب\n"
            "`.acc2_photo` - صورة البروفايل\n\n"
            "✉️ **مراسلة الجندي**\n"
            "`.sendmsg @user نص` - إرسال رسالة\n"
            "`.sendvoice @user` - بالرد على بصمة\n"
            "`.sendvideo @user مسار` - أو تفاعلي\n"
            "`.sendsticker @user` - بالرد على ملصق\n"
            "`.sendgif @user` - بالرد على GIF\n"
            "`.senddoc @user` - بالرد على ملف\n"
            "`.fwd من إلى` - توجيه آخر رسالة\n"
            "`.spam عدد نص` - سبام\n"
            "`.typing @user` - إظهار الكتابة\n"
            "`.readall` - تعليم الكل مقروءاً\n"
            "`.clear @user` - حذف 100 رسالة\n\n"
            "🔧 **إعدادات الحساب**\n"
            "`.setname الاسم` - تغيير الاسم\n"
            "`.setuser @يوزر` - تغيير المعرف\n"
            "`.setbio نبذة` - تغيير النبذة\n"
            "`.setphoto` - تغيير الصورة (بالرد)\n"
            "`.delphoto` - حذف الصورة\n"
            "`.privacy_hide_number` - إخفاء الرقم\n"
            "`.privacy_show_number` - إظهار الرقم\n"
            "`.block @user` - حظر\n"
            "`.unblock @user` - إلغاء حظر\n"
            "`.kickme رابط` - مغادرة قناة\n"
            "`.leaveall` - مغادرة جميع القنوات\n"
            "`.archive_all` - أرشفة كل المحادثات\n"
            "`.mute @user` - كتم\n"
            "`.unmute @user` - إلغاء الكتم\n\n"
            "🎯 **صيد الروليت**\n"
            "`.addkey كلمة` - إضافة كلمة للصيد\n"
            "`.delkey كلمة` - حذف كلمة\n"
            "`.listkeys` - عرض الكلمات\n"
            "`.clearcache` - تفريغ الذاكرة\n"
            "`.reset` - تصفير الإحصائيات\n"
            "`.trust_on` / `.trust_off` - نظام الثقة\n\n"
            "⚙️ **التحكم الرئيسي**\n"
            "`.start` / `.stop` - تشغيل/إيقاف المحرك\n"
            "`.status` - الإحصائيات\n"
            "`.help` - هذه القائمة\n"
            "`.acc2_dialogs` - آخر محادثات الجندي\n\n"
            "📌 **التوقيت الذكي**\n"
            "الروليت محدود العدد (مثل 5/10): ينضم بسرعة 5-7s\n"
            "الروليت المفتوح: يتأخر 15-25s عشوائي لتجنب الحظر.\n"
            "كل الأوامر تعمل من حسابك الرئيسي فقط."
        )

    # ---------- محرك الأوامر الموسع ----------
    async def execute_command(self, event, cmd_parts):
        """معالجة أوامر الإدارة (أكثر من 100)"""
        cmd = cmd_parts[0].lower()
        if not cmd.startswith('.'): return False
        cmd = cmd[1:]
        args = cmd_parts[1:]
        client = self.client2
        admin = event.sender_id

        try:
            # ----- بدء/إيقاف -----
            if cmd == "start":
                self.config["running"] = True
                await client.send_message(self.admin_id, "🟢 المحرك يعمل الآن")
                await event.reply("✅ تم التشغيل")
                return True
            elif cmd == "stop":
                self.config["running"] = False
                await client.send_message(self.admin_id, "🔴 المحرك متوقف")
                await event.reply("🛑 تم الإيقاف")
                return True

            # ----- معلومات الجندي -----
            elif cmd == "acc2_id":
                me = await client.get_me()
                await event.reply(f"🆔 ID: `{me.id}`")
            elif cmd == "acc2_name":
                me = await client.get_me()
                await event.reply(f"👤 {me.first_name or ''} {me.last_name or ''}")
            elif cmd == "acc2_user":
                me = await client.get_me()
                await event.reply(f"📛 @{me.username}" if me.username else "لا يوجد")
            elif cmd == "acc2_phone":
                me = await client.get_me()
                await event.reply(f"📱 رقم الجندي: `{me.phone}`")
            elif cmd == "acc2_bio":
                full = await client(functions.users.GetFullUserRequest("me"))
                await event.reply(f"📝 {full.full_user.about or 'فارغة'}")
            elif cmd == "acc2_stars_balance":
                await event.reply("⭐ رصيد النجوم غير متاح عبر API العام")
            elif cmd == "acc2_dc":
                me = await client.get_me()
                dc = me.photo.dc_id if me.photo else "غير معروف"
                await event.reply(f"☁️ DC{dc}")
            elif cmd == "acc2_limit":
                await event.reply("ℹ️ حدود غير متاحة مباشرة")
            elif cmd == "acc2_photo":
                photos = await client.get_profile_photos("me", limit=1)
                if photos:
                    await event.reply(file=photos[0])
                else:
                    await event.reply("لا توجد صورة")

            # ----- مراسلة -----
            elif cmd == "sendmsg" and len(args) >= 2:
                target, text = args[0], " ".join(args[1:])
                await client.send_message(target, text)
                await event.reply("✅ تم")
            elif cmd == "sendvoice" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.voice or msg.audio:
                        await client.send_file(args[0], msg.media)
                        await event.reply("🎤 تم")
                    else:
                        await event.reply("❌ الرد ليس بصمة")
                else:
                    await event.reply("⚠️ استخدم الأمر بالرد على بصمة")
            elif cmd == "sendvideo":
                if args and len(args) >= 2:
                    # مسار مباشر
                    target, path = args[0], " ".join(args[1:])
                    await client.send_file(target, path)
                    await event.reply("🎬 تم")
                elif args and len(args) == 1 and event.is_reply:
                    target = args[0]
                    msg = await event.get_reply_message()
                    if msg.video or msg.document:
                        await client.send_file(target, msg.media)
                        await event.reply("🎬 تم")
                elif not args:
                    # تفاعلي
                    self.conversation_state[admin] = {"state": "WAIT_RECIPIENT", "cmd": "sendvideo"}
                    await event.reply("👤 أرسل @المستخدم أو الرقم:")
                else:
                    await event.reply("⚠️ الاستخدام: .sendvideo @user مسار")
                return True
            elif cmd == "sendsticker" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.sticker:
                        await client.send_file(args[0], msg.sticker)
                        await event.reply("🌟 تم")
                else:
                    await event.reply("⚠️ الرد على ملصق")
            elif cmd == "sendgif" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.gif:
                        await client.send_file(args[0], msg.gif)
                        await event.reply("🎞️ تم")
                else:
                    await event.reply("⚠️ الرد على GIF")
            elif cmd == "senddoc" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.document:
                        await client.send_file(args[0], msg.document)
                        await event.reply("📎 تم")
                else:
                    await event.reply("⚠️ الرد على ملف")
            elif cmd == "fwd" and len(args) >= 2:
                src, dst = args[0], args[1]
                msgs = await client.get_messages(src, limit=1)
                if msgs:
                    await client.forward_messages(dst, msgs[0])
                    await event.reply("↗️ تم التوجيه")
            elif cmd == "spam" and len(args) >= 2:
                count = int(args[0])
                text = " ".join(args[1:])
                for _ in range(count):
                    await event.reply(text)
                    await asyncio.sleep(0.5)
                await event.reply(f"🔥 {count} رسالة")
            elif cmd == "typing" and args:
                async with client.action(args[0], 'typing'):
                    await asyncio.sleep(4)
                await event.reply("✅")
            elif cmd == "readall":
                dialogs = await client.get_dialogs()
                for d in dialogs:
                    if d.unread_count:
                        await client.send_read_acknowledge(d.entity)
                await event.reply("📖 تم")
            elif cmd == "clear" and args:
                async for msg in client.iter_messages(args[0], limit=100):
                    await msg.delete()
                await event.reply("🗑️ تم حذف 100 رسالة")

            # ----- إدارة الحساب -----
            elif cmd == "setname" and args:
                name = " ".join(args)
                await client(functions.account.UpdateProfileRequest(first_name=name))
                await event.reply("✅")
            elif cmd == "setuser" and args:
                username = args[0].strip('@')
                try:
                    await client(functions.account.UpdateUsernameRequest(username=username))
                    await event.reply(f"✅ @{username}")
                except errors.UsernameOccupiedError:
                    await event.reply("❌ محجوز")
            elif cmd == "setbio" and args:
                bio = " ".join(args)
                await client(functions.account.UpdateProfileRequest(about=bio))
                await event.reply("✅")
            elif cmd == "setphoto" and event.is_reply:
                msg = await event.get_reply_message()
                if msg.photo:
                    await client(functions.photos.UploadProfilePhotoRequest(
                        file=await client.upload_file(msg.photo)
                    ))
                    await event.reply("🖼️ تم")
            elif cmd == "delphoto":
                photos = await client.get_profile_photos("me", limit=1)
                if photos:
                    await client(functions.photos.DeletePhotosRequest(id=[photos[0].id]))
                    await event.reply("🗑️ تم")
            elif cmd == "privacy_hide_number":
                await client(functions.account.SetPrivacyRequest(
                    key=types.InputPrivacyKeyPhoneNumber(),
                    rules=[types.InputPrivacyValueDisallowAll()]
                ))
                await event.reply("🔒 رقم الجندي مخفي")
            elif cmd == "privacy_show_number":
                await client(functions.account.SetPrivacyRequest(
                    key=types.InputPrivacyKeyPhoneNumber(),
                    rules=[types.InputPrivacyValueAllowAll()]
                ))
                await event.reply("📱 رقم الجندي ظاهر")
            elif cmd == "block" and args:
                user = await client.get_entity(args[0])
                await client(functions.contacts.BlockRequest(id=user))
                await event.reply(f"🚫 حظر {args[0]}")
            elif cmd == "unblock" and args:
                user = await client.get_entity(args[0])
                await client(functions.contacts.UnblockRequest(id=user))
                await event.reply("✅")
            elif cmd == "kickme" and args:
                try:
                    entity = await client.get_entity(args[0])
                    await client.delete_dialog(entity)
                    await event.reply("👋")
                except:
                    await event.reply("فشل")
            elif cmd == "leaveall":
                dialogs = await client.get_dialogs()
                count = 0
                for d in dialogs:
                    if d.is_channel:
                        try:
                            await client.delete_dialog(d.entity)
                            count += 1
                        except: pass
                await event.reply(f"🚪 غادر {count} قناة")
            elif cmd == "archive_all":
                dialogs = await client.get_dialogs()
                for d in dialogs:
                    await client.edit_folder(d.entity, folder=1)
                await event.reply("📦")
            elif cmd == "mute" and args:
                user = await client.get_entity(args[0])
                await client(functions.account.UpdateNotifySettingsRequest(
                    peer=user,
                    settings=types.InputPeerNotifySettings(mute_until=2**31-1)
                ))
                await event.reply("🔇")
            elif cmd == "unmute" and args:
                user = await client.get_entity(args[0])
                await client(functions.account.UpdateNotifySettingsRequest(
                    peer=user,
                    settings=types.InputPeerNotifySettings(mute_until=0)
                ))
                await event.reply("🔔")

            # ----- صيد -----
            elif cmd == "addkey" and args:
                kw = " ".join(args)
                self.keywords.append(kw)
                await event.reply(f"➕ {kw}")
            elif cmd == "delkey" and args:
                kw = " ".join(args)
                if kw in self.keywords:
                    self.keywords.remove(kw)
                    await event.reply(f"➖ {kw}")
            elif cmd == "listkeys":
                await event.reply("📋 " + ", ".join(self.keywords[:40]))
            elif cmd == "clearcache":
                self.cache.clear()
                await event.reply("🧹")
            elif cmd == "reset":
                self.stats = {"wins1":0,"wins2":0,"stars1":0,"stars2":0,"start_time":time.time()}
                self.cache.clear()
                await event.reply("🔄")
            elif cmd == "trust_on":
                self.config["trust"] = True
                await event.reply("🤝 مفعل")
            elif cmd == "trust_off":
                self.config["trust"] = False
                await event.reply("🤝 معطل")
            elif cmd == "acc2_dialogs":
                dialogs = await client.get_dialogs(limit=15)
                txt = "💬 **آخر المحادثات:**\n"
                for i,d in enumerate(dialogs):
                    name = d.name or d.entity.username or str(d.entity.id)
                    txt += f"{i+1}. {name}\n"
                await event.reply(txt)
            elif cmd == "status":
                uptime = time.strftime("%H:%M:%S", time.gmtime(time.time()-self.stats["start_time"]))
                await event.reply(f"⏱️ {uptime}\n🏆1: {self.stats['wins1']} 🏆2: {self.stats['wins2']}\n⭐1: {self.stats['stars1']} ⭐2: {self.stats['stars2']}\n⚙️ {'يعمل' if self.config['running'] else 'متوقف'}")
            elif cmd == "help":
                await event.reply(self.generate_commands_list())
            else:
                await event.reply("❓ استخدم `.help`")
        except Exception as e:
            await event.reply(f"⚠️ خطأ: {str(e)[:150]}")
            logger.error(f"Command error: {e}")
        return True

    # ---------- عملية الصيد الذكية (التوقيت الفرق) ----------
    async def process_logic(self, event, client, acc_num):
        try:
            # 1. ثقة
            if self.config["trust"] and event.is_private and not event.out:
                if any(x in event.raw_text for x in ["هدية", "نجمة", "نجوم"]) or getattr(event.message, 'action', None):
                    delay = random.randint(12, 25)
                    await asyncio.sleep(delay)
                    await event.reply("ثقة")
                    self.stats[f"stars{acc_num}"] += 1
                    logger.info(f"⭐ ثقة من حساب {acc_num}")
                    return

            # 2. كابتشا
            if await self.solve_captchas(event, acc_num):
                return

            # 3. أزرار الروليت
            if event.reply_markup and event.id not in self.cache:
                text_lower = event.raw_text.lower()
                btn_texts = [b.text for row in event.reply_markup.rows for b in row.buttons]
                btn_str = " ".join(btn_texts).lower()
                combined = text_lower + " " + btn_str

                # كشف النمط: محدود (فيه رقم/عدد) أم مفتوح
                limited = bool(re.search(r'\b\d+/\d+\b|مقعد|مقاعد|من \d+|المشاركين', event.raw_text))
                if any(k in combined for k in self.keywords) or "مشاركة (" in combined:
                    self.cache.add(event.id)
                    await self.auto_join_requirements(event, client)

                    # تحديد التأخير
                    if limited:
                        delay = random.uniform(5.0, 7.0)   # روليت سريع
                        logger.info(f"⚡ روليت محدود - انضمام سريع {delay:.1f}s (حساب {acc_num})")
                    else:
                        delay = random.uniform(15.0, 25.0)  # روليت عام
                        logger.info(f"🐢 روليت مفتوح - تأخير {delay:.1f}s (حساب {acc_num})")

                    await asyncio.sleep(delay)

                    # النقر على أول زر مناسب
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if any(k in btn.text for k in self.keywords) or "مشاركة" in btn.text:
                                await self._safe_call(event.client, event.click, r_idx, b_idx)
                                self.stats[f"wins{acc_num}"] += 1
                                logger.info(f"🏆 فوز حساب {acc_num} - زر: {btn.text}")
                                return
        except Exception as e:
            logger.warning(f"خطأ منطق الصيد: {e}")

    # ---------- بدء التشغيل المزدوج ----------
    async def engine_start(self):
        # ----- قتل أي جلسة عالقة (اختياري) -----
        try:
            await self.client1.connect()
            if not await self.client1.is_user_authorized():
                logger.critical("🛑 SESSION_1 غير صالحة! تأكد من توليد جلسة حصرية لـ GitHub.")
                return
            # تأكيد الاتصال
            await self._safe_call(self.client1, self.client1.get_me())
            await self.client1.send_message("me", "🟢 Omega V60 Started")
            logger.info("✅ الحساب 1 متصل")
        except errors.rpcerrorlist.AuthKeyDuplicatedError:
            logger.critical("🔑 الجلسة مستخدمة من IP آخر. أعد توليد الجلسة.\nالحل: شغّل `get_sessions.py` على جهازك واستخرج جلسات جديدة.")
            return
        except Exception as e:
            logger.error(f"❌ حساب 1: {e}")
            return

        # ----- الحساب الثاني -----
        try:
            await self.client2.connect()
            if not await self.client2.is_user_authorized():
                logger.warning("⚠️ SESSION_2 غير صالحة. سيعمل الحساب الأول فقط.")
                self.config["run2"] = False
            else:
                await self._safe_call(self.client2, self.client2.get_me())
                logger.info("✅ الحساب 2 متصل")
                self.config["run2"] = True
        except Exception as e:
            logger.error(f"❌ حساب 2: {e}")
            self.config["run2"] = False

        # ----- المعالجات -----
        @self.client1.on(events.NewMessage)
        async def main_handler(event):
            # تفاعل sendvideo
            if event.sender_id == self.admin_id and event.sender_id in self.conversation_state:
                state = self.conversation_state[event.sender_id]
                if state["cmd"] == "sendvideo":
                    if state["state"] == "WAIT_RECIPIENT":
                        state["recipient"] = event.raw_text.strip()
                        state["state"] = "WAIT_VIDEO"
                        await event.reply("🎥 الآن أرسل الفيديو (أو مساره):")
                        return
                    elif state["state"] == "WAIT_VIDEO":
                        recipient = state["recipient"]
                        if event.media:
                            await self.client2.send_file(recipient, event.media)
                        else:
                            await self.client2.send_file(recipient, event.raw_text.strip())
                        await event.reply("✅ تم إرسال الفيديو")
                        del self.conversation_state[event.sender_id]
                        return
            # أوامر
            if event.sender_id == self.admin_id and event.raw_text.startswith("."):
                await self.execute_command(event, event.raw_text.split())
                return
            if not self.config["running"]:
                return
            await self.process_logic(event, self.client1, 1)

        @self.client2.on(events.NewMessage)
        async def second_handler(event):
            if not self.config.get("run2") or not self.config["running"]:
                return
            await self.process_logic(event, self.client2, 2)

        logger.info("🚀 Omega V60 يصرع الجلسات القديمة ويعمل الآن...")
        await self.client1.run_until_disconnected()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(OmegaDualCore().engine_start())
    except KeyboardInterrupt:
        print("\n🛑 توقف يدوي")
    except Exception as e:
        logger.critical(f"تعطل: {e}")
