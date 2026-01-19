# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import re
from pyrogram import enums, types
from che import app, db

class Utilities:
    def __init__(self):
        self.active_calls_cache = 0

    def format_eta(self, seconds: int) -> str:
        if not seconds or not isinstance(seconds, int):
            return "0s"
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d} min"
        else:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h}:{m:02d}:{s:02d} h"

    def format_size(self, bytes: int) -> str:
        if not bytes:
            return "0 KB"
        if bytes >= 1024**3:
            return f"{bytes / 1024 ** 3:.2f} GB"
        elif bytes >= 1024**2:
            return f"{bytes / 1024 ** 2:.2f} MB"
        else:
            return f"{bytes / 1024:.2f} KB"

    def to_seconds(self, time: str) -> int:
        if not time:
            return 0
        try:
            if ":" not in time:
                return 0
            parts = [int(p) for p in time.strip().split(":")]
            return sum(value * 60**i for i, value in enumerate(reversed(parts)))
        except:
            return 0

    def get_url(self, message_1: types.Message) -> str | None:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        
        target_types = [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]

        for message in messages:
            entities = message.entities or message.caption_entities or []
            text_to_parse = message.text or message.caption or ""

            for entity in entities:
                if entity.type in target_types:
                    link = None
                    if entity.type == enums.MessageEntityType.TEXT_LINK:
                        link = entity.url
                    elif entity.type == enums.MessageEntityType.URL:
                        link = text_to_parse[entity.offset : entity.offset + entity.length]
                    if link:
                        return link.split("&si")[0].split("?si")[0]
        return None

    async def extract_user(self, msg: types.Message) -> types.User | None:
        if msg.reply_to_message:
            return msg.reply_to_message.from_user
        if msg.entities:
            for e in msg.entities:
                if e.type == enums.MessageEntityType.TEXT_MENTION:
                    return e.user
        if msg.text:
            try:
                if m := re.search(r"@(\w{5,32})", msg.text):
                    return await app.get_users(m.group(0))
                if m := re.search(r"\b\d{6,15}\b", msg.text):
                    return await app.get_users(int(m.group(0)))
            except:
                pass
        return None

    async def play_log(self, message: types.Message, title: str, duration: str) -> None:
        # 1. LOGGER ID KONTROLÜ
        LOGGER_ID = getattr(app, "logger", None)
        
        if not LOGGER_ID:
            try:
                from config import LOGGER_ID as CONFIG_LOGGER_ID
                LOGGER_ID = CONFIG_LOGGER_ID
            except:
                LOGGER_ID = None
        
        if not LOGGER_ID:
            return

        chat_id = message.chat.id
        
        # 2. ORİJİNAL AKTİF SES SAYISI (Canlı Veri)
        # db.active_calls hafızadaki sözlüktür, anlıktır.
        try:
            aktif_ses = len(db.active_calls)
        except Exception:
            aktif_ses = 0

        # 3. GRUP BAŞLIĞI GÜNCELLEME (Gereksiz API isteklerini önlemek için cache kontrolü)
        if aktif_ses != self.active_calls_cache:
            self.active_calls_cache = aktif_ses
            try:
                await app.set_chat_title(LOGGER_ID, f"🎧 AKTİF SES: {aktif_ses}")
            except:
                # Yetki yoksa veya çok hızlı değişiyorsa hata vermemesi için pass
                pass

        # 4. ORİJİNAL TOPLAM GRUP SAYISI (Veritabanı Sayımı)
        try:
            # count_documents({}) doğrudan veritabanındaki kayıt sayısını verir. En kesin yöntemdir.
            toplam_grup = await db.chatsdb.count_documents({})
        except Exception:
            # Eğer veritabanı bağlantısında sorun varsa yedek yöntem
            try:
                toplam_grup = len(await db.get_chats())
            except:
                toplam_grup = "Hata"

        # 5. DİĞER BİLGİLER
        try:
            uye_sayisi = await app.get_chat_members_count(chat_id)
        except:
            uye_sayisi = "Gizli"

        if message.chat.username:
            grup_link = f"@{message.chat.username}"
        else:
            try:
                invite = await app.export_chat_invite_link(chat_id)
                grup_link = f"[Bağlantı]({invite})"
            except:
                grup_link = "Bağlantı Yok"

        user = message.from_user
        mention = user.mention if user else "Anonim"
        user_id = user.id if user else 0
        
        # 6. LOG METNİ OLUŞTURMA
        logger_text = (
            f"🎵 **OYNATMA GÜNLÜĞÜ**\n\n"
            f"📍 **Grup Bilgileri**\n"
            f"├ Ad: {message.chat.title}\n"
            f"├ ID: `{chat_id}`\n"
            f"├ Üye: {uye_sayisi}\n"
            f"└ Link: {grup_link}\n\n"
            f"👤 **Talep Eden**\n"
            f"├ Kullanıcı: {mention}\n"
            f"└ ID: `{user_id}`\n\n"
            f"💿 **Şarkı Bilgisi**\n"
            f"├ Ad: {title}\n"
            f"└ Süre: {duration}\n\n"
            f"📊 **Bot İstatistikleri**\n"
            f"├ 🏠 Toplam Grup: {toplam_grup}\n"
            f"└ 🎧 Aktif Ses: {aktif_ses}"
        )

        # 7. LOG GÖNDERME
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    LOGGER_ID,
                    text=logger_text,
                    disable_web_page_preview=True,
                )
            except Exception as e:
                print(f"❌ Log gönderilemedi: {e}")

    async def send_log(self, m: types.Message, chat: bool = False) -> None:
        LOGGER_ID = getattr(app, "logger", None)
        if not LOGGER_ID:
            try:
                from config import LOGGER_ID as CONFIG_LOGGER_ID
                LOGGER_ID = CONFIG_LOGGER_ID
            except:
                return

        try:
            if chat:
                user = m.from_user
                text = f"**SOĞBET LOGU**\n\nID: `{m.chat.id}`\nBaşlık: {m.chat.title}\nKullanıcı: {user.mention if user else 'Anonim'}"
            else:
                text = f"**KULLANICI LOGU**\n\nID: `{m.from_user.id}`\nAd: {m.from_user.mention}"
            
            await app.send_message(chat_id=LOGGER_ID, text=text)
        except Exception:
            pass
