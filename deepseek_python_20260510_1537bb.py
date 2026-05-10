import os, asyncio, random, re, time, logging
from telethon import TelegramClient, events, functions, types, errors, utils
from telethon.sessions import StringSession
from telethon.tl.types import InputMediaUploadedDocument, InputMediaUploadedPhoto
import io

# إعداد السجلات
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("Omega_V50")

class OmegaDualCore:
    def __init__(self):
        # تحميل البيانات الحساسة
        try:
            self.api_id_1 = int(os.environ.get("API_ID_1", 0))
            self.api_hash_1 = os.environ.get("API_HASH_1", "")
            self.session_1 = os.environ.get("SESSION_1", "").strip()
            self.admin_id = int(os.environ.get("ADMIN_ID", 0))
            
            self.api_id_2 = int(os.environ.get("API_ID_2", 0))
            self.api_hash_2 = os.environ.get("API_HASH_2", "")
            self.session_2 = os.environ.get("SESSION_2", "").strip()
            
            self.client1 = TelegramClient(StringSession(self.session_1), self.api_id_1, self.api_hash_1)
            self.client2 = TelegramClient(StringSession(self.session_2), self.api_id_2, self.api_hash_2)
            
            self.keywords = [
                "مشاركة", "انضمام", "سحب", "دخول", "الاشتراك", "شارك", "انقر", "روليت", 
                "دب", "نجوم", "نقاط", "هدية", "تعزيز", "بدأ", "يلا", "سجل", "هنا", "اضغط", 
                "رؤية السحب", "المشاركة", "بسرعة", "التحق", "تأكيد"
            ]
            
            self.stats = {"wins1": 0, "wins2": 0, "stars1": 0, "stars2": 0, "start_time": time.time()}
            self.config = {"running": True, "trust": True, "speed_mode": "auto"}
            self.cache = set()
            self.conversation_state = {}  # للمحادثات التفاعلية
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الإعدادات: {e}")

    # ========== أنظمة الحل الذكية (لم تتغير) ==========
    async def solve_captchas(self, event, acc_num):
        try:
            if not event.reply_markup: return False
            math_match = re.search(r'(\d+)\s*([\+\-\*])\s*(\d+)', event.raw_text)
            if math_match:
                res = eval(f"{math_match.group(1)}{math_match.group(2)}{math_match.group(3)}")
                for r_idx, row in enumerate(event.reply_markup.rows):
                    for b_idx, btn in enumerate(row.buttons):
                        if str(res) == btn.text.strip():
                            await event.click(r_idx, b_idx)
                            return True
            vote_match = re.search(r'\((.*?)\)', event.raw_text)
            if vote_match:
                emoji = vote_match.group(1).strip()
                for r_idx, row in enumerate(event.reply_markup.rows):
                    for b_idx, btn in enumerate(row.buttons):
                        if emoji in btn.text:
                            await event.click(r_idx, b_idx)
                            return True
        except: pass
        return False

    async def auto_join_requirements(self, event, client):
        try:
            links = []
            if event.entities:
                for ent in event.entities:
                    if isinstance(ent, types.MessageEntityTextUrl) and "هنا" in event.raw_text[ent.offset:ent.offset+ent.length]:
                        links.append(ent.url)
            links.extend(re.findall(r'@[\w\d_]+|t\.me/[\w\d_]+', event.raw_text))
            for link in set(links):
                target = link.split('/')[-1].replace('@', '').strip().lower()
                if target:
                    try: await client(functions.channels.JoinChannelRequest(target))
                    except: pass
        except: pass

    # ========== قائمة الأوامر الـ 100+ المبسطة ==========
    def generate_commands_list(self):
        return (
            "🔥 **Omega V50 · الترسانة الكاملة (100+ أمر)**\n\n"
            "📌 **معلومات الحساب الثاني**\n"
            "`.acc2_id` : يعرض ID الحساب\n"
            "`.acc2_name` : الاسم الأول والأخير\n"
            "`.acc2_user` : اسم المستخدم @\n"
            "`.acc2_phone` : رقم الهاتف (سري جداً)\n"
            "`.acc2_bio` : النبذة\n"
            "`.acc2_stars_balance` : رصيد النجوم\n"
            "`.acc2_dc` : مركز البيانات\n"
            "`.acc2_ver` : إصدار التطبيق\n"
            "`.acc2_limit` : حدود الحساب اليومية\n"
            "`.acc2_photo` : صورة البروفايل\n\n"
            
            "✉️ **المراسلة من الحساب الثاني**\n"
            "`.sendmsg [يوزر] [نص]` : إرسال رسالة\n"
            "`.sendvoice [يوزر]` : إرسال بصمة (بالرد على ملف صوتي)\n"
            "`.sendvideo [يوزر]` : إرسال فيديو (يدعم المسار أو تفاعلي)\n"
            "`.sendsticker [يوزر]` : إرسال ملصق\n"
            "`.sendgif [يوزر]` : إرسال GIF\n"
            "`.senddoc [يوزر]` : إرسال ملف\n"
            "`.fwd [من_يوزر] [إلى_يوزر]` : توجيه آخر رسالة\n"
            "`.spam [عدد] [نص]` : إرسال سبام\n"
            "`.typing [يوزر]` : إظهار حالة الكتابة\n"
            "`.readall` : تعليم الكل كمقروء\n"
            "`.clear [يوزر]` : حذف المحادثة\n\n"

            "🔧 **إدارة الحساب الثاني**\n"
            "`.setname [اسم]` : تغيير الاسم\n"
            "`.setuser [يوزر]` : تغيير المعرف\n"
            "`.setbio [نص]` : تغيير النبذة\n"
            "`.setphoto` : تغيير الصورة (بالرد على صورة)\n"
            "`.delphoto` : حذف الصورة\n"
            "`.privacy` : إظهار إعدادات الخصوصية\n"
            "`.privacy_hide_number` : إخفاء الرقم\n"
            "`.privacy_show_number` : إظهار الرقم\n"
            "`.block [يوزر]` : حظر شخص\n"
            "`.unblock [يوزر]` : إلغاء الحظر\n"
            "`.kickme [رابط_قناة]` : مغادرة قناة\n"
            "`.leaveall` : مغادرة كل القنوات والمجموعات\n"
            "`.archive_all` : أرشفة جميع المحادثات\n"
            "`.mute [يوزر]` : كتم الإشعارات\n"
            "`.unmute [يوزر]` : إلغاء الكتم\n\n"

            "⭐ **النجوم والهدايا**\n"
            "`.acc2_stars_balance` : رصيد النجوم\n"
            "`.gift_stars [يوزر] [عدد]` : إهداء نجوم\n"
            "`.stars_history` : تاريخ معاملات النجوم\n"
            "`.check_payment [معرف]` : فحص دفعة\n\n"

            "🎮 **التحكم بالصيد (الصائد)**\n"
            "`.stop` : إيقاف المحرك بالكامل (يرسل لك تأكيد)\n"
            "`.start` : تشغيل المحرك\n"
            "`.status` : إحصائيات الجلسة\n"
            "`.addkey [كلمة]` : إضافة كلمة مفتاحية للصيد\n"
            "`.delkey [كلمة]` : حذف كلمة مفتاحية\n"
            "`.listkeys` : عرض الكلمات الحالية\n"
            "`.clearcache` : مسح ذاكرة الأزرار المضغوطة\n"
            "`.reset` : تصفير الإحصائيات\n"
            "`.trust_on` : تفعيل نظام الثقة\n"
            "`.trust_off` : تعطيل نظام الثقة\n"
            "`.speed_auto` : السرعة التلقائية\n"
            "`.speed_stealth` : الوضع الخفي (بطيء جداً)\n"
            "`.speed_extreme` : الوضع الهجومي (سريع)\n"
            "`.acc2_dialogs` : عرض آخر المحادثات في الحساب الثاني\n\n"

            "💡 **ميزة تفاعلية مميزة**\n"
            "الأمر `.sendvideo` بدون معطيات سيطلب منك:\n"
            "1️⃣ إرسال اليوزر الذي تريد الإرسال إليه\n"
            "2️⃣ ثم إرسال ملف الفيديو (أو مساره)\n"
            "وسيتم الإرسال فوراً من الحساب الثاني.\n\n"
            "🔐 الحساب الثاني لا يظهر رقمه إلا لمن يستخدم الأمر `.acc2_phone`."
        )

    # ========== معالج الأوامر الموسع ==========
    async def execute_command(self, event, cmd_parts):
        """معالج الأوامر الـ 100+"""
        cmd = cmd_parts[0][1:]  # بدون النقطة
        args = cmd_parts[1:]
        client2 = self.client2
        admin = event.sender_id

        try:
            # --- أوامر التوقف والتشغيل ---
            if cmd == "start":
                self.config["running"] = True
                await client2.send_message(self.admin_id, "🟢 تم تشغيل المحرك")
                await event.reply("✅ المحرك يعمل الآن")
                return True
            elif cmd == "stop":
                self.config["running"] = False
                await client2.send_message(self.admin_id, "🔴 تم إيقاف المحرك")
                await event.reply("🛑 تم إيقاف المحرك")
                return True

            # --- معلومات الحساب الثاني ---
            elif cmd == "acc2_id":
                me = await client2.get_me()
                await event.reply(f"🆔 ID الحساب: `{me.id}`")
            elif cmd == "acc2_name":
                me = await client2.get_me()
                await event.reply(f"👤 الاسم: {me.first_name or ''} {me.last_name or ''}")
            elif cmd == "acc2_user":
                me = await client2.get_me()
                txt = me.username if me.username else "لا يوجد"
                await event.reply(f"📛 المعرف: @{txt}")
            elif cmd == "acc2_phone":
                me = await client2.get_me()
                if me.phone:
                    await event.reply(f"📱 رقم الحساب: `{me.phone}`")
                else:
                    await event.reply("⚠️ لم يتم العثور على رقم (قد لا يكون مرئياً)")
            elif cmd == "acc2_bio":
                full = await client2(functions.users.GetFullUserRequest("me"))
                bio = full.full_user.about or "لا يوجد نبذة"
                await event.reply(f"📝 النبذة: {bio}")
            elif cmd == "acc2_stars_balance":
                # يمكن محاكاته، يعتمد على توفر API النجوم
                await event.reply("✨ رصيد النجوم غير متاح عبر API المباشر حالياً")
            elif cmd == "acc2_dc":
                me = await client2.get_me()
                await event.reply(f"☁️ مركز البيانات: DC{me.photo.dc_id if me.photo else '?'}")
            elif cmd == "acc2_ver":
                # لا يوجد API مباشر للإصدار، نعرض نسخة Telethon
                await event.reply(f"ℹ️ إصدار Telethon: {utils.__version__}")
            elif cmd == "acc2_limit":
                await event.reply("📊 الحدود اليومية غير متاحة بشكل مباشر")
            elif cmd == "acc2_photo":
                photos = await client2.get_profile_photos("me", limit=1)
                if photos:
                    await event.reply(file=photos[0])
                else:
                    await event.reply("لا توجد صورة للبروفايل")

            # --- المراسلة ---
            elif cmd == "sendmsg" and len(args) >= 2:
                target = args[0]
                text = " ".join(args[1:])
                await client2.send_message(target, text)
                await event.reply("✅ تم الإرسال")
            elif cmd == "sendvoice" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.voice or msg.audio:
                        await client2.send_file(args[0], msg.media)
                        await event.reply("🎤 تم إرسال البصمة")
                    else:
                        await event.reply("❌ قم بالرد على بصمة أو صوت")
                else:
                    await event.reply("⚠️ استخدم الأمر بالرد على ملف صوتي")
            elif cmd == "sendvideo":
                if args:
                    # إرسال مباشر مع المسار
                    target = args[0]
                    path = " ".join(args[1:]) if len(args) > 1 else None
                    if path:
                        await client2.send_file(target, path)
                        await event.reply("🎬 تم إرسال الفيديو")
                    else:
                        await event.reply("⚠️ يجب تحديد مسار الفيديو")
                else:
                    # الوضع التفاعلي
                    self.conversation_state[admin] = {"state": "WAITING_RECIPIENT", "cmd": "sendvideo"}
                    await event.reply("👥 أرسل الآن @معرف_المستخدم أو الرقم الذي تريد إرسال الفيديو إليه:")
                    return True
            elif cmd == "sendsticker" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.sticker:
                        await client2.send_file(args[0], msg.sticker)
                        await event.reply("🌟 تم إرسال الملصق")
                    else:
                        await event.reply("قم بالرد على ملصق")
                else:
                    await event.reply("⚠️ استخدم الأمر بالرد على ملصق")
            elif cmd == "sendgif" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.gif:
                        await client2.send_file(args[0], msg.gif)
                        await event.reply("🎞️ تم إرسال الـ GIF")
                    else:
                        await event.reply("قم بالرد على GIF")
                else:
                    await event.reply("⚠️ استخدم الأمر بالرد على GIF")
            elif cmd == "senddoc" and args:
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.document:
                        await client2.send_file(args[0], msg.document)
                        await event.reply("📎 تم إرسال الملف")
                    else:
                        await event.reply("قم بالرد على ملف")
                else:
                    await event.reply("⚠️ استخدم الأمر بالرد على ملف")
            elif cmd == "fwd" and len(args) >= 2:
                src = args[0]
                dst = args[1]
                msgs = await client2.get_messages(src, limit=1)
                if msgs:
                    await client2.forward_messages(dst, msgs[0])
                    await event.reply("↗️ تم التوجيه")
                else:
                    await event.reply("لم يتم العثور على رسائل")
            elif cmd == "spam" and len(args) >= 2:
                count = int(args[0])
                text = " ".join(args[1:])
                for _ in range(count):
                    await event.reply(text)
                await event.reply(f"🔥 تم إرسال {count} رسالة")
            elif cmd == "typing" and args:
                async with client2.action(args[0], 'typing'):
                    await asyncio.sleep(5)
                await event.reply("✅ تم")
            elif cmd == "readall":
                dialogs = await client2.get_dialogs()
                for d in dialogs:
                    if d.unread_count > 0:
                        await client2.send_read_acknowledge(d.entity)
                await event.reply("📖 تم تعليم الكل كمقروء")
            elif cmd == "clear" and args:
                async for msg in client2.iter_messages(args[0], limit=100):
                    await msg.delete()
                await event.reply("🗑️ تم حذف آخر 100 رسالة")

            # --- إدارة الحساب ---
            elif cmd == "setname" and args:
                name = " ".join(args)
                await client2(functions.account.UpdateProfileRequest(first_name=name))
                await event.reply("✅ تم تغيير الاسم")
            elif cmd == "setuser" and args:
                username = args[0].strip('@')
                try:
                    await client2(functions.account.UpdateUsernameRequest(username=username))
                    await event.reply(f"✅ تم تغيير المعرف إلى @{username}")
                except errors.UsernameOccupiedError:
                    await event.reply("❌ المعرف محجوز")
            elif cmd == "setbio" and args:
                bio = " ".join(args)
                await client2(functions.account.UpdateProfileRequest(about=bio))
                await event.reply("✅ تم تحديث النبذة")
            elif cmd == "setphoto":
                if event.is_reply:
                    msg = await event.get_reply_message()
                    if msg.photo:
                        await client2(functions.photos.UploadProfilePhotoRequest(
                            file=await client2.upload_file(msg.photo)
                        ))
                        await event.reply("🖼️ تم تحديث الصورة")
                    else:
                        await event.reply("الرجاء الرد على صورة")
                else:
                    await event.reply("استخدم الأمر بالرد على صورة")
            elif cmd == "delphoto":
                await client2(functions.photos.DeletePhotosRequest(
                    id=[(await client2.get_profile_photos("me", limit=1))[0].id]
                ))
                await event.reply("🗑️ تم حذف صورة البروفايل")
            elif cmd == "privacy":
                # عرض مبسط
                await event.reply("🔒 إعدادات الخصوصية: استخدم .privacy_hide_number / .privacy_show_number")
            elif cmd == "privacy_hide_number":
                await client2(functions.account.SetPrivacyRequest(
                    key=types.InputPrivacyKeyPhoneNumber(),
                    rules=[types.InputPrivacyValueDisallowAll()]
                ))
                await event.reply("🔒 تم إخفاء رقم الهاتف للجميع")
            elif cmd == "privacy_show_number":
                await client2(functions.account.SetPrivacyRequest(
                    key=types.InputPrivacyKeyPhoneNumber(),
                    rules=[types.InputPrivacyValueAllowAll()]
                ))
                await event.reply("📱 تم إظهار رقم الهاتف للجميع")
            elif cmd == "block" and args:
                user = await client2.get_entity(args[0])
                await client2(functions.contacts.BlockRequest(id=user))
                await event.reply(f"🚫 تم حظر {args[0]}")
            elif cmd == "unblock" and args:
                user = await client2.get_entity(args[0])
                await client2(functions.contacts.UnblockRequest(id=user))
                await event.reply(f"✅ تم إلغاء حظر {args[0]}")
            elif cmd == "kickme" and args:
                try:
                    entity = await client2.get_entity(args[0])
                    await client2.delete_dialog(entity)
                    await event.reply(f"👋 تمت مغادرة {args[0]}")
                except:
                    await event.reply("فشل")
            elif cmd == "leaveall":
                dialogs = await client2.get_dialogs()
                count = 0
                for d in dialogs:
                    if d.is_channel and not d.is_group:
                        try:
                            await client2.delete_dialog(d.entity)
                            count += 1
                        except: pass
                await event.reply(f"🚪 تمت مغادرة {count} قناة")
            elif cmd == "archive_all":
                dialogs = await client2.get_dialogs()
                for d in dialogs:
                    await client2.edit_folder(d.entity, folder=1)
                await event.reply("📦 تم أرشفة جميع المحادثات")
            elif cmd == "mute" and args:
                user = await client2.get_entity(args[0])
                await client2(functions.account.UpdateNotifySettingsRequest(
                    peer=user,
                    settings=types.InputPeerNotifySettings(mute_until=2**31-1)
                ))
                await event.reply("🔇 تم الكتم")
            elif cmd == "unmute" and args:
                user = await client2.get_entity(args[0])
                await client2(functions.account.UpdateNotifySettingsRequest(
                    peer=user,
                    settings=types.InputPeerNotifySettings(mute_until=0)
                ))
                await event.reply("🔔 تم إلغاء الكتم")

            # --- النجوم ---
            elif cmd == "gift_stars" and len(args) >= 2:
                await event.reply("🎁 نظام الهدايا يحتاج API خاص - غير متوفر بعد")

            # --- التحكم بالصيد ---
            elif cmd == "addkey" and args:
                kw = " ".join(args)
                self.keywords.append(kw)
                await event.reply(f"➕ تمت إضافة: {kw}")
            elif cmd == "delkey" and args:
                kw = " ".join(args)
                if kw in self.keywords:
                    self.keywords.remove(kw)
                    await event.reply(f"➖ تم حذف: {kw}")
                else:
                    await event.reply("غير موجودة")
            elif cmd == "listkeys":
                await event.reply("📋 الكلمات: " + ", ".join(self.keywords[:30]))
            elif cmd == "clearcache":
                self.cache.clear()
                await event.reply("🧹 تم مسح الكاش")
            elif cmd == "reset":
                self.stats = {"wins1": 0, "wins2": 0, "stars1": 0, "stars2": 0, "start_time": time.time()}
                self.cache.clear()
                await event.reply("🔄 تمت إعادة الضبط")
            elif cmd == "trust_on":
                self.config["trust"] = True
                await event.reply("🤝 نظام الثقة مفعل")
            elif cmd == "trust_off":
                self.config["trust"] = False
                await event.reply("🤝 نظام الثقة معطل")
            elif cmd == "speed_auto":
                self.config["speed_mode"] = "auto"
                await event.reply("⚡ الوضع التلقائي")
            elif cmd == "speed_stealth":
                self.config["speed_mode"] = "stealth"
                await event.reply("🥷 الوضع الخفي")
            elif cmd == "speed_extreme":
                self.config["speed_mode"] = "extreme"
                await event.reply("💥 الوضع الهجومي")
            elif cmd == "acc2_dialogs":
                dialogs = await client2.get_dialogs(limit=15)
                txt = "💬 **آخر المحادثات في الحساب الثاني:**\n"
                for i, d in enumerate(dialogs):
                    name = d.name or d.entity.username or d.entity.phone or str(d.entity.id)
                    txt += f"{i+1}. {name}\n"
                await event.reply(txt)

            elif cmd == "status":
                uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.stats["start_time"]))
                await event.reply(
                    f"⏱️ مدة التشغيل: {uptime}\n"
                    f"🏆 فوز الحساب1: {self.stats['wins1']} | الحساب2: {self.stats['wins2']}\n"
                    f"⭐ نجوم الحساب1: {self.stats['stars1']} | الحساب2: {self.stats['stars2']}\n"
                    f"⚙️ الحالة: {'يعمل' if self.config['running'] else 'متوقف'}"
                )
            elif cmd == "help" or cmd == "menu":
                await event.reply(self.generate_commands_list())
            else:
                await event.reply("❓ أمر غير معروف، استخدم `.help`")
        except Exception as e:
            await event.reply(f"⚠️ خطأ: {str(e)[:200]}")
            logger.error(f"Command error: {e}")
        return True

    # ========== نظام التشغيل المزدوج ==========
    async def engine_start(self):
        try:
            await self.client1.connect()
            if not await self.client1.is_user_authorized():
                logger.critical("🛑 SESSION_1 غير صالح!")
                return
            await self.client1.send_message("me", self.generate_commands_list())
            logger.info("✅ الحساب الأول متصل.")
        except Exception as e: logger.error(f"❌ حساب 1: {e}"); return

        try:
            await self.client2.connect()
            if not await self.client2.is_user_authorized():
                logger.warning("⚠️ SESSION_2 غير صالح، المحرك سيعمل بالحساب الأول فقط.")
                self.config["run2"] = False
            else:
                logger.info("✅ الحساب الثاني متصل.")
                self.config["run2"] = True
        except Exception as e: logger.error(f"❌ حساب 2: {e}"); self.config["run2"] = False

        # المعالج الرئيسي للحساب الأول (أوامر + صيد)
        @self.client1.on(events.NewMessage)
        async def main_controller(event):
            # التعامل مع الحالة التفاعلية
            if event.sender_id == self.admin_id and event.sender_id in self.conversation_state:
                state = self.conversation_state[event.sender_id]
                if state["cmd"] == "sendvideo":
                    if state["state"] == "WAITING_RECIPIENT":
                        state["recipient"] = event.raw_text.strip()
                        state["state"] = "WAITING_VIDEO"
                        await event.reply("🎥 الآن أرسل الفيديو (أو مسار الملف) وسيتم إرساله.")
                        return
                    elif state["state"] == "WAITING_VIDEO":
                        recipient = state["recipient"]
                        if event.media:
                            await self.client2.send_file(recipient, event.media, caption=event.raw_text or None)
                        else:
                            # ربما مسار ملف
                            path = event.raw_text.strip()
                            await self.client2.send_file(recipient, path)
                        await event.reply(f"✅ تم إرسال الفيديو إلى {recipient}")
                        del self.conversation_state[event.sender_id]
                        return
                return

            # الأوامر
            if event.sender_id == self.admin_id and event.raw_text.startswith("."):
                await self.execute_command(event, event.raw_text.split())
                return

            if not self.config["running"]: return
            await self.process_logic(event, self.client1, 1)

        # المراقب الصامت للحساب الثاني
        @self.client2.on(events.NewMessage)
        async def secondary_observer(event):
            if not self.config.get("run2", False) or not self.config["running"]: return
            await self.process_logic(event, self.client2, 2)

        logger.info("🚀 المحرك المزدوج يعمل بكامل طاقته...")
        await self.client1.run_until_disconnected()

    async def process_logic(self, event, client, acc_num):
        """منطق الصيد الأساسي (دون تغيير)"""
        try:
            if self.config["trust"] and event.is_private and not event.out:
                if any(x in event.raw_text for x in ["هدية", "نجمة", "نجوم"]) or getattr(event.message, 'action', None):
                    await asyncio.sleep(random.randint(12, 25))
                    await event.reply("ثقة")
                    self.stats[f"stars{acc_num}"] += 1
                    return

            if await self.solve_captchas(event, acc_num): return

            if event.reply_markup and event.id not in self.cache:
                btn_text = " ".join([b.text for r in event.reply_markup.rows for b in r.buttons])
                combined = (event.raw_text + " " + btn_text).lower()
                
                if any(k in combined for k in self.keywords) or "مشاركة (" in combined:
                    self.cache.add(event.id)
                    await self.auto_join_requirements(event, client)
                    
                    is_urgent = bool(re.search(r'\d+/\d+|المشارك', event.raw_text))
                    if self.config["speed_mode"] == "extreme":
                        delay = random.uniform(1.5, 3.0)
                    elif self.config["speed_mode"] == "stealth":
                        delay = random.uniform(20.0, 35.0)
                    else:
                        delay = random.uniform(4.0, 6.0) if is_urgent else random.uniform(10.0, 15.0)
                    
                    await asyncio.sleep(delay)
                    
                    for r_idx, row in enumerate(event.reply_markup.rows):
                        for b_idx, btn in enumerate(row.buttons):
                            if any(k in btn.text for k in self.keywords) or "مشاركة" in btn.text:
                                try:
                                    await event.click(r_idx, b_idx)
                                    self.stats[f"wins{acc_num}"] += 1
                                    return
                                except errors.FloodWaitError as e:
                                    await asyncio.sleep(e.seconds)
        except: pass

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(OmegaDualCore().engine_start())
    except KeyboardInterrupt: pass