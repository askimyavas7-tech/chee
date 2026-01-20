import os
import random
import time
import datetime
import asyncio
from random import shuffle
from typing import List, Tuple, Union
from datetime import datetime as dt
from pyrogram import client, filters
from pyrogram.enums import *
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
    ChatMember,
    CallbackQuery,
    ChatMemberUpdated,
)
from che import app
from config import LOGGER_ID, OWNER_ID
# kumsal.py dosyasının ArchMusic.plugins.tools altında olduğundan emin olun
from che.plugins.cheetiket import *

che_tagger = {} # Ana etiketleme durum sözlüğü
users = []
members = {} # Eros modülü için
chatMode = [] # Chatmode modülü için
chat_mode_users = {} # Chatmode yetki kontrolü için

# ---------------------------------------------------------------------------------
# ETİKETLEME KOMUTLARI
# ---------------------------------------------------------------------------------

@app.on_message(filters.command("tag") & filters.group)
async def tag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    args = message.command

    if len(args) > 1:
        msg_content = " ".join(args[1:])
    elif message.reply_to_message:
        msg_content = message.reply_to_message.text
        if msg_content is None:
            await message.reply("❗ Eski mesajı göremiyorum!")
            return
    else:
        msg_content = ""

    total_members = 0
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if not user.is_bot and not user.is_deleted:
            total_members += 1
    user = message.from_user
    chat = message.chat
    
    await app.send_message(LOGGER_ID, f"""
Etiket işlemi bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Tekli Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
"""
    )
    
    num = 1
    estimated_time = (total_members // num) * 5

    start_msg = await message.reply(f"""
**Üye etiketleme işlemi başlıyor.**

**Silinen hesapları ve botları atlayacak**

👥 __Toplam Etiketlenecek Üye Sayısı: {total_members}__
⏳ __Tahmini Süre: {estimated_time // 60} dakika__
""")
    
    che_tagger[message.chat.id] = start_msg.id
    nums = 1
    usrnum = 0
    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0
    usrtxt = ""
    
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if user.is_bot:
            skipped_bots += 1
            continue
        if user.is_deleted:
            skipped_deleted += 1
            continue
        usrnum += 1
        total_tagged += 1
        
        # DÜZELTME: ID kalktı, mention eklendi
        usrtxt += f"• {user.mention}"
        
        # İptal kontrolü
        if message.chat.id not in che_tagger or che_tagger[message.chat.id] != start_msg.id:
            return
            
        if usrnum == nums:
            await app.send_message(message.chat.id, f" **{msg_content}**\n\n{usrtxt}")
            usrnum = 0
            usrtxt = ""
            await asyncio.sleep(5)

    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]

    await app.send_message(message.chat.id, f"""
**Üye etiketleme işlemi tamamlandı** ✅

👥 __Etiketlenen üye: {total_tagged}__
🤖 __Atlanılan Bot Sayısı: {skipped_bots}__
💣 __Atlanılan Silinen Hesap Sayısı: {skipped_deleted}__
""")


@app.on_message(filters.command("guntag") & filters.group)
async def guntag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    start_msg = await message.reply("☀️ **Günaydın mesajları başlıyor!** 👋")
    che_tagger[message.chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    async for member in app.get_chat_members(message.chat.id):
        if message.chat.id not in che_tagger or che_tagger[message.chat.id] != start_msg.id:
            return

        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # DÜZELTME: ID kalktı, mention eklendi
        text = random.choice(guntag_messages).format(user=u.mention)
        await app.send_message(message.chat.id, text)
        await asyncio.sleep(2)

    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]

    await app.send_message(message.chat.id, f"""
**Günaydın mesajları tamamlandı!** ✅

👥 __Mesaj gönderilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")


@app.on_message(filters.command("gecetag") & filters.group)
async def gecetag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    start_msg = await message.reply("🌙 **İyi geceler mesajları başlıyor!** 😴")
    che_tagger[chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    await app.send_message(LOGGER_ID, f"""
Etiket işlemi bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Gece Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
"""
    )

    async for member in app.get_chat_members(chat.id):
        if chat.id not in che_tagger or che_tagger[chat.id] != start_msg.id:
            return

        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # DÜZELTME: ID kalktı, mention eklendi
        text = random.choice(gece_messages).format(user=u.mention)
        await app.send_message(chat.id, text)
        await asyncio.sleep(2)
        
    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]

    await app.send_message(chat.id, f"""
**İyi geceler mesajları tamamlandı!** ✅

👥 __Mesaj gönderilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")

@app.on_message(filters.command("kurttag") & filters.group)
async def kurttag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    await app.send_message(LOGGER_ID, f"""
Kurt oyunu daveti bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Tekli Kurt Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
""")

    start_msg = await message.reply("🐺 **Kurt oyunu başlıyor!** Silinen hesapları ve botları atlayacak.")
    che_tagger[message.chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    async for member in app.get_chat_members(message.chat.id):
        if message.chat.id not in che_tagger or che_tagger[message.chat.id] != start_msg.id:
            return

        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # DÜZELTME: ID kalktı, mention eklendi
        await app.send_message(message.chat.id, f"{u.mention}, {random.choice(messages)}")
        await asyncio.sleep(2)
        
    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]

    await app.send_message(message.chat.id, f"""
**Kurt oyunu davetleri tamamlandı** ✅

👥 __Davet edilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")


@app.on_message(filters.command("tabutag") & filters.group)
async def tabutag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    await app.send_message(LOGGER_ID, f"""
Tabu oyunu daveti bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Tekli Tabu Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
"""
    )

    start_msg = await message.reply("🎲 **Tabu oyunu başlıyor!** Silinen hesapları ve botları atlayacak.")
    che_tagger[message.chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    async for member in app.get_chat_members(message.chat.id):
        if message.chat.id not in che_tagger or che_tagger[message.chat.id] != start_msg.id:
            return

        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # DÜZELTME: ID kalktı, mention eklendi
        await app.send_message(
            message.chat.id,
            f"{u.mention}, {random.choice(tabu_messages)}"
        )
        await asyncio.sleep(2)

    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]

    await app.send_message(message.chat.id, f"""
**Tabu davetleri tamamlandı** ✅

👥 __Davet edilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")
    
@app.on_message(filters.command("anonimtag") & filters.group)
async def anonimtag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    user = message.from_user
    chat = message.chat

    await app.send_message(LOGGER_ID, f"""
Anonim oyunu daveti bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Tekli Anonim Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
""")

    start_msg = await message.reply("🎭 **Anonim oyunu başlıyor!** Silinen hesapları ve botları atlayacak.")
    che_tagger[message.chat.id] = start_msg.id

    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0

    async for member in app.get_chat_members(message.chat.id):
        if message.chat.id not in che_tagger or che_tagger[message.chat.id] != start_msg.id:
            return
        
        u = member.user
        if u.is_bot:
            skipped_bots += 1
            continue
        if u.is_deleted:
            skipped_deleted += 1
            continue

        total_tagged += 1
        # DÜZELTME: ID kalktı, mention eklendi
        await app.send_message(
            message.chat.id,
            f"{u.mention}, {random.choice(anonim_messages)}"
        )
        await asyncio.sleep(2)

    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]

    await app.send_message(message.chat.id, f"""
**Anonim davetleri tamamlandı** ✅

👥 __Davet edilen üye: {total_tagged}__
🤖 __Atlanılan Bot: {skipped_bots}__
💣 __Atlanılan Silinen Hesap: {skipped_deleted}__
""")
    
@app.on_message(filters.command("utag") & filters.group)
async def utag(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return

    args = message.command

    if len(args) > 1:
        msg_content = " ".join(args[1:])
    elif message.reply_to_message:
        msg_content = message.reply_to_message.text
        if msg_content is None:
            await message.reply("❗ Eski mesajı göremiyorum!")
            return
    else:
        msg_content = ""

    total_members = 0
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if not user.is_bot and not user.is_deleted:
            total_members += 1
    user = message.from_user
    chat = message.chat
    
    await app.send_message(LOGGER_ID, f"""
Etiket işlemi bildirimi.

Kullanan : {user.mention} [`{user.id}`]
Etiket Tipi : Çoklu Tag

Grup : {chat.title}
Grup İD : `{chat.id}`

Sebep : {message.text}
"""
    )
    
    num = 5
    estimated_time = (total_members // num) * 5

    start_msg = await message.reply(f"""
**Üye etiketleme işlemi başlıyor.**

**Silinen hesapları ve botları atlayacak**

👥 __Toplam Etiketlenecek Üye Sayısı: {total_members}__
⏳ __Tahmini Süre: {estimated_time // 60} dakika__
""")
    
    che_tagger[message.chat.id] = start_msg.id
    nums = 5
    usrnum = 0
    skipped_bots = 0
    skipped_deleted = 0
    total_tagged = 0
    usrtxt = ""
    
    async for member in app.get_chat_members(message.chat.id):
        user = member.user
        if user.is_bot:
            skipped_bots += 1
            continue
        if user.is_deleted:
            skipped_deleted += 1
            continue
        usrnum += 1
        total_tagged += 1
        
        # DÜZELTME: ID kalktı, mention eklendi (Çoklu Tag)
        usrtxt += f"• {user.mention}\n"
        
        # İptal kontrolü
        if message.chat.id not in che_tagger or che_tagger[message.chat.id] != start_msg.id:
            return
            
        if usrnum == nums:
            await app.send_message(message.chat.id, f" **{msg_content}**\n\n{usrtxt}")
            usrnum = 0
            usrtxt = ""
            await asyncio.sleep(5)
            
    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]

    await app.send_message(message.chat.id, f"""
**Üye etiketleme işlemi tamamlandı** ✅

👥 __Etiketlenen üye: {total_tagged}__
🤖 __Atlanılan Bot Sayısı: {skipped_bots}__
💣 __Atlanılan Silinen Hesap Sayısı: {skipped_deleted}__
""")

@app.on_message(filters.command("cancel") & filters.group)
async def stop(app, message):
    admins = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if message.from_user.id not in admins:
        await message.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return
        
    if message.chat.id in che_tagger:
        del che_tagger[message.chat.id]
        await message.reply("⛔ __Etiketleme işlemi durduruldu!__")
    else:
        await message.reply("❗ __Etiketleme işlemi şu anda aktif değil.__")

# ---------------------------------------------------------------------------------
# EROS MODÜLÜ
# ---------------------------------------------------------------------------------

@app.on_message(filters.command("eros", ["/", ""]) & filters.group)
async def _eros(client: app, message: Message):
    chatID = message.chat.id
    statu = []
    if chatID in statu:
        return await message.reply("Aşıklar listesi güncelleniyor. Lütfen bekleyiniz..")

    async def scrapper(bot: app, msg: Message):
        chat_id = msg.chat.id
        temp = {}
        try:
            statu.append(chat_id)
            async for member in bot.get_chat_members(chat_id, limit=200):
                member: ChatMember

                if member.user.is_bot:
                    continue
                if member.user.is_deleted:
                    continue

                temp[member.user.id] = member.user
                await asyncio.sleep(0.05)

            members[chat_id]["members"] = temp
            members[chat_id]["lastUpdate"] = dt.now()
            statu.remove(chat_id)
            return True
        except Exception as e:
            print(e)
            return False

    async def ship_(users: dict):
        list_ = list(users.keys())
        random.shuffle(list_)

        member1ID = random.choice(list_)
        member2ID = random.choice(list_)

        while member1ID == member2ID:
            member2ID = random.choice(list_)

        member1: User = users[member1ID]
        member2: User = users[member2ID]

        mention1 = member1.mention
        mention2 = member2.mention

        text = f"**💘 ᴇʀᴏs'ᴜɴ ᴏᴋᴜ ᴀᴛɪʟᴅɪ.\n• ᴀsɪᴋʟᴀʀ  :\n\n{mention1} {random.choice(galp)} {mention2}**\n\n`ᴜʏᴜᴍʟᴜʟᴜᴋ ᴏʀᴀɴɪ: %{random.randint(0, 100)}`"
        return text

    if chatID not in members:
        members[chatID] = {}

    lastUpdate: dt = members[chatID].get("lastUpdate")
    if lastUpdate:
        now = dt.now()
        diff = now - lastUpdate
        if diff.seconds > 3600 * 4:
            msg = await message.reply(
                "Aşıklar listesi güncelleniyor, lütfen bekleyiniz..."
            )
            status = await scrapper(client, message)
            if status:
                await msg.delete()
                text = await ship_(members[chatID]["members"])
                return await message.reply(text)
            else:
                return await msg.edit(
                    "Bir hata oluştu, lütfen daha sonra tekrar deneyiniz."
                )
        else:
            text = await ship_(members[chatID]["members"])
            return await message.reply(text)

    else:
        msg = await message.reply("Aşıklar listesi güncelleniyor, lütfen bekleyiniz...")
        status = await scrapper(client, message)
        if status:
            await msg.delete()
            text = await ship_(members[chatID]["members"])
            return await message.reply(text)
        else:
            return await msg.edit(
                "Bir hata oluştu, lütfen daha sonra tekrar deneyiniz."
            )

# ---------------------------------------------------------------------------------
# CHATMODE MODÜLÜ
# ---------------------------------------------------------------------------------

@app.on_message(filters.command("chatmode") & filters.group)
async def chat_mode_controller(bot: app, msg: Message):
    admins = []
    async for member in bot.get_chat_members(msg.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        admins.append(member.user.id)

    if msg.from_user.id not in admins:
        await msg.reply("❗ Bu komutu kullanmak için yönetici olmalısınız!")
        return
        
    chat_id = msg.chat.id
    chat = msg.chat
    commands = msg.command
    chat_mode_users[chat_id] = msg.from_user.id 

    await bot.send_message(LOGGER_ID, f""" 
#CHATMODE KULLANILDI
👤 Kullanan : {msg.from_user.mention}
💥 Kullanıcı Id : {msg.from_user.id}
🪐 Kullanılan Grup : {chat.title}
💡 Grup ID : {chat.id}
◀️ Grup Link : @{chat.username}
""")
    
    if len(commands) == 1:
        status = "✅ Açık" if chat_id in chatMode else "❌ Kapalı"
        return await msg.reply(
            f"Durum : {status}\n\nSohbet modu kullanıcıların mesajlarına cevap verir.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Aç", callback_data="on"),
                        InlineKeyboardButton("Kapat", callback_data="off"),
                    ]
                ]
            ),
        )

@app.on_callback_query(filters.regex("^(on|off)$"))
async def chat_mode_callback(bot: app, cb: CallbackQuery):
    chat_id = cb.message.chat.id
    user_id = cb.from_user.id
    cmd = cb.data

    if chat_id not in chat_mode_users or chat_mode_users[chat_id] != user_id:
        await cb.answer("Bu işlemi yapma yetkiniz yok.", show_alert=True)
        return

    if cmd == "on":
        if chat_id in chatMode:
            await cb.edit_message_text("Sohbet modu zaten açık.")
        else:
            chatMode.append(chat_id)
            await cb.edit_message_text("Sohbet modu açıldı.")
    elif cmd == "off":
        if chat_id not in chatMode:
            await cb.edit_message_text("Sohbet modu zaten kapalı.")
        else:
            chatMode.remove(chat_id)
            await cb.edit_message_text("Sohbet modu kapatıldı.")

    await cb.answer()


@app.on_message(filters.group & filters.text & ~filters.command("chatmode"), group=10)
async def chatModeHandler(bot: app, msg: Message):
    def lower(text):
        return str(text.translate({ord("I"): ord("ı"), ord("İ"): ord("i")})).lower()

    def kontrol(query: Union[str, list], text: str) -> bool:
        if isinstance(query, str):
            return query in text.split()
        elif isinstance(query, list):
            for q in query:
                if q in text.split():
                    return True
            return False
        else:
            return False

    if msg.chat.id not in chatMode or msg.from_user.is_self:
        return

    text = lower(msg.text) 

    reply = None

    if text.startswith("Aynur"): 
        reply = random.choice(Aynur)
        await asyncio.sleep(0.06)
    
    elif kontrol(["selam", "slm", "sa", "selamlar", "selamm"], text):
        reply = random.choice(slm)
        await asyncio.sleep(0.06)    
    elif kontrol(["sahip"], text):
        reply = random.choice(sahip)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["naber"], text):
        reply = random.choice(naber)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["pelin"], text):
        reply = random.choice(pelin)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["nasılsın"], text):
        reply = random.choice(nasılsın)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["tm","tamam","tmm"], text):
        reply = random.choice(tm)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["sus","suuss","suss"], text):
        reply = random.choice(sus)
        await asyncio.sleep(0.06)  
    
    elif kontrol(["merhaba","mrb","meraba"], text):
        reply = random.choice(merhaba)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["yok"], text):
        reply = random.choice(yok)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["dur"], text):
        reply = random.choice(dur)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["bot", "botu"], text):
        reply = random.choice(bott)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["napıyorsun"], text):
        reply = random.choice(napıyorsun)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["takılıyorum","takılıyom"], text):
        reply = random.choice(takılıyorum)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["he"], text):
        reply = random.choice(he)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["hayır"], text):
        reply = random.choice(hayır)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["tm"], text):
        reply = random.choice(tm)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["nerdesin"], text):
        reply = random.choice(nerdesin)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["özledim"], text):
        reply = random.choice(özledim)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["bekle"], text):
        reply = random.choice(bekle)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["tünaydın"], text):
        reply = random.choice(tünaydın)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["günaydın"], text):
        reply = random.choice(günaydın)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["sohbetler"], text):
        reply = random.choice(sohbetler)
        await asyncio.sleep(0.06)        
            
    elif kontrol(["konuşalım","konusalım"], text):
        reply = random.choice(konuşalım)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["saat"], text):
        reply = random.choice(saat)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["geceler"], text):
        reply = random.choice(geceler)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["şaka"], text):
        reply = random.choice(şaka)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["kimsin"], text):
        reply = random.choice(kimsin)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["günler"], text):
        reply = random.choice(günler)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["tanımıyorum"], text):
        reply = random.choice(tanımıyorum)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["konuşma"], text):
        reply = random.choice(konuşma)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["teşekkürler","tesekkürler","tşkr"], text):
        reply = random.choice(teşekkürler)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["eyvallah","eywl"], text):
        reply = random.choice(eyvallah)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["sağol"], text):
        reply = random.choice(sağol)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["amk","aq","mg","mk"], text):
        reply = random.choice(amk)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["yoruldum"], text):
        reply = random.choice(yoruldum)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["yaş"], text):
        reply = random.choice(yaş)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["eşşek","eşek"], text):
        reply = random.choice(eşek)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["canım"], text):
        reply = random.choice(canım)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["aşkım","askım","ask"], text):
        reply = random.choice(aşkım)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["uyu"], text):
        reply = random.choice(uyu)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["nereye","nere"], text):
        reply = random.choice(nereye)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["naber"], text):
        reply = random.choice(naber)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["küstüm","küsüm"], text):
        reply = random.choice(küstüm)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["peki"], text):
        reply = random.choice(peki)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["ne","nee","neee","ney"], text):
        reply = random.choice(ne)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["takım"], text):
        reply = random.choice(takım)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["benimle","bnmle"], text):
        reply = random.choice(benimle)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["seviyormusun","seviyomusun"], text):
        reply = random.choice(seviyormusun)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["nediyon"], text):
        reply = random.choice(nediyon)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["özür"], text):
        reply = random.choice(özür)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["niye"], text):
        reply = random.choice(niye)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["bilmiyorum","bilmiyom","bilmiyos"], text):
        reply = random.choice(bilmiyorum)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["küsme"], text):
        reply = random.choice(küsme)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["kumsal"], text):
        reply = random.choice(kumsal)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["nerelisin"], text):
        reply = random.choice(nerelisin)
        await asyncio.sleep(0.06)  
    
    elif kontrol(["sevgilin"], text):
        reply = random.choice(sevgilin)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["olur"], text):
        reply = random.choice(olur)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["olmas","olmaz"], text):
        reply = random.choice(olmaz)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["nasıl"], text):
        reply = random.choice(nasıl)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["hayatım"], text):
        reply = random.choice(hayatım)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["cus"], text):
        reply = random.choice(cus)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["vallaha","valla","vallahi"], text):
        reply = random.choice(vallaha)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["yo"], text):
        reply = random.choice(yo)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["hayırdır"], text):
        reply = random.choice(hayırdır)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["of"], text):
        reply = random.choice(of)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["aynen"], text):
        reply = random.choice(aynen)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["ağla"], text):
        reply = random.choice(ağla)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["ağlama"], text):
        reply = random.choice(ağlama)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["sex","seks"], text):
        reply = random.choice(sex)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["evet"], text):
        reply = random.choice(evet)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["hmm","hm","hımm","hmmm"], text):
        reply = random.choice(hmm)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["hıhım"], text):
        reply = random.choice(hıhım)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["git"], text):
        reply = random.choice(git)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["komedi"], text):
        reply = random.choice(komedi)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["knka","kanka"], text):
        reply = random.choice(knka)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["ban"], text):
        reply = random.choice(ban)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["sen"], text):
        reply = random.choice(sen)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["hiç"], text):
        reply = random.choice(hiç)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["aç","ac","açç"], text):
        reply = random.choice(aç)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["barışalım","batısalım"], text):
        reply = random.choice(barışalım)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["şimdi"], text):
        reply = random.choice(şimdi)
        await asyncio.sleep(0.06)    
        
    elif kontrol(["varoş"], text):
        reply = random.choice(varoş)
        await asyncio.sleep(0.06)        
                
    elif kontrol(["arkadaş","arkadas"], text):
        reply = random.choice(arkadaş)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["sus","suss","suus"], text):
        reply = random.choice(sus)
        await asyncio.sleep(0.06)        
        
    elif kontrol(["üzüldüm","üşüldüm"], text):
        reply = random.choice(üzüldüm)
        await asyncio.sleep(0.06)  
        
    elif kontrol(["kötü"], text):
        reply = random.choice(kötü)
        await asyncio.sleep(0.06)    
    
    elif kontrol(["akşamlar"], text):
        reply = random.choice(akşamlar)
        await asyncio.sleep(0.06)    
        
    try:
        await msg.reply(reply)
    except Exception as e:
        print(e)

    msg.continue_propagation()

# ---------------------------------------------------------------------------------
# OYUN KOMUTLARI
# ---------------------------------------------------------------------------------

@app.on_message(filters.command(commandList))
async def games(c: app, m: Message):
    
    "🎲", "🎯", "🏀", "⚽", "🎳", "🎰"

    command = m.command[0]

    if command == "zar":
        return await c.send_dice(m.chat.id, emoji="🎲",
                                 reply_markup=InlineKeyboardMarkup(
                                     [
                                         [
                                             InlineKeyboardButton(
                                                 "Tekrar Oyna ♻️", callback_data="zar"
                                             ),
                                         ]
                                     ]
                                 )
                                 )

    elif command == "dart":
        return await c.send_dice(m.chat.id, emoji="🎯",
                                 reply_markup=InlineKeyboardMarkup(
                                     [
                                         [
                                             InlineKeyboardButton(
                                                 "Tekrar Oyna ♻️", callback_data="dart"
                                             ),
                                         ]
                                     ]
                                 )
                                 )

    elif command == "basket":
        return await c.send_dice(m.chat.id, emoji="🏀",
                                 reply_markup=InlineKeyboardMarkup(
                                     [
                                         [
                                             InlineKeyboardButton(
                                                 "Tekrar Oyna ♻️", callback_data="basket"
                                             ),
                                         ]
                                     ]
                                 )
                                 )

    elif command == "futbol":
        return await c.send_dice(m.chat.id, emoji="⚽",
                                 reply_markup=InlineKeyboardMarkup(
                                     [
                                         [
                                             InlineKeyboardButton(
                                                 "Tekrar Oyna ♻️", callback_data="futbol"
                                             ),
                                         ]
                                     ]
                                 )
                                 )

    elif command == "bowling":
        return await c.send_dice(m.chat.id, emoji="🎳",
                                 reply_markup=InlineKeyboardMarkup(
                                     [
                                         [
                                             InlineKeyboardButton(
                                                 "Tekrar Oyna ♻️", callback_data="bowling"
                                             ),
                                         ]
                                     ]
                                 )
                                 )

    elif command == "slot":
        return await c.send_dice(m.chat.id, emoji="🎰",
                                 reply_markup=InlineKeyboardMarkup(
                                     [
                                         [
                                             InlineKeyboardButton(
                                                 "Tekrar Oyna ♻️", callback_data="slot"
                                             ),
                                         ]
                                     ]
                                 )
                                 )

    elif command == "para":
        return await m.reply(
            "**Yazı 🪙**" if random.randint(0, 1) == 0 else "**Tura 🪙**"
        )

    elif command == "mani":
        return await m.reply_text(random.choice(mani))

    elif command == "saka":
        return await m.reply_text(f"**{random.choice(espri)}**")

    elif command == "d":
        return await m.reply_text(
            f"**✅ Doğruluk mu ? 🔪 Cesaret mi ? \n\n{m.from_user.mention} Doğruluk sorusu seçti !\n\n{random.choice(D_LİST)}**"
        )

    elif command == "c":
        return await m.reply_text(
            f"**✅ Doğruluk mu ? 🔪 Cesaret mi ? \n\n{m.from_user.mention} Cesaret sorusu seçti !\n\n{random.choice(C_LİST)}**"
        )


    return

# ---------------------------------------------------------------------------------
# OYUN CALLBACKLERİ
# ---------------------------------------------------------------------------------

@app.on_callback_query(filters.regex("zar"))
async def zar(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎲",
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [
                                       InlineKeyboardButton(
                                           "Tekrar Oyna ♻️", callback_data="zar"
                                       ),
                                   ]
                               ]
                           )
                           )

@app.on_callback_query(filters.regex("dart"))
async def dart(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎯",
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [
                                       InlineKeyboardButton(
                                           "Tekrar Oyna ♻️", callback_data="dart"
                                       ),
                                   ]
                               ]
                           )
                           )

@app.on_callback_query(filters.regex("basket"))
async def basket(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🏀",
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [
                                       InlineKeyboardButton(
                                           "Tekrar Oyna ♻️", callback_data="basket"
                                       ),
                                   ]
                               ]
                           )
                           )

@app.on_callback_query(filters.regex("futbol"))
async def futbol(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="⚽",
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [
                                       InlineKeyboardButton(
                                           "Tekrar Oyna ♻️", callback_data="futbol"
                                       ),
                                   ]
                               ]
                           )
                           )

@app.on_callback_query(filters.regex("bowling"))
async def bowling(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎳",
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [
                                       InlineKeyboardButton(
                                           "Tekrar Oyna ♻️", callback_data="bowling"
                                       ),
                                   ]
                               ]
                           )
                           )

@app.on_callback_query(filters.regex("slot"))
async def slot(client: app, query: CallbackQuery):
    await client.send_dice(query.message.chat.id, emoji="🎰",
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [
                                       InlineKeyboardButton(
                                           "Tekrar Oyna ♻️", callback_data="slot"
                                       ),
                                   ]
                               ]
                           )
                           )

# ---------------------------------------------------------------------------------
# DİĞER EĞLENCE KOMUTLARI
# ---------------------------------------------------------------------------------

@app.on_message(filters.command(["slap", "sille"]) & filters.group)
async def slap(bot: app, message: Message):
    
    chat = message.chat
    if not message.reply_to_message:
        await message.reply_text("🚫 **Bir kullanıcıya cevap verin!**")
        return
    if message.reply_to_message.from_user.id == OWNER_ID:
        await message.reply_text(f"{random.choice(dontslapown)}")
        return
    if message.reply_to_message.from_user.id == app.id:
        await message.reply_text(f"{random.choice(dontslapme)}")
        return
    

    atan = message.from_user
    yiyen = message.reply_to_message.from_user

    # DÜZELTME: ID kalktı, mention eklendi
    atan_mesaj = atan.mention
    yiyen_mesaj = yiyen.mention

    goktug = random.choice(slapmessage)
    await message.reply_text(
        goktug.format(atan_mesaj, yiyen_mesaj),
    )

    await bot.send_message(
        LOGGER_ID, 
        f"""
👤 Kullanan : {atan.mention}
💥 Kullanıcı Id : {atan.id}
🪐 Kullanılan Grup : {chat.title}
💡 Grup ID : {chat.id}
◀️ Grup Link : @{chat.username}
📚 Kullanılan Modül : {message.text}
"""
    )

@app.on_message(filters.command(["oner"]) & filters.group)
async def oner(bot: app, message: Message):
    
    chat = message.chat
    if not message.reply_to_message:
        await message.reply_text("🚫 **Bir kullanıcıya cevap verin!**")
        return
    if message.reply_to_message.from_user.id == OWNER_ID:
        await message.reply_text(f"{random.choice(sarki1)}")
        return
    if message.reply_to_message.from_user.id == app.id:
        await message.reply_text(f"{random.choice(sarki2)}")
        return
    

    atan = message.from_user
    yiyen = message.reply_to_message.from_user

    # DÜZELTME: ID kalktı, mention eklendi
    atan_mesaj = atan.mention
    yiyen_mesaj = yiyen.mention

    goktug = random.choice(sarkilar)
    await message.reply_text(
        goktug.format(atan_mesaj, yiyen_mesaj),
    )

    await bot.send_message(
        LOGGER_ID,
        f"""
👤 Kullanan : {atan.mention}
💥 Kullanıcı Id : {atan.id}
🪐 Kullanılan Grup : {chat.title}
💡 Grup ID : {chat.id}
◀️ Grup Link : @{chat.username}
📚 Kullanılan Modül : Şarkı Öneri
"""
    )
