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
        # === DEBUG BAŞLANGICI ===
        LOGGER_ID = getattr(app, "logger", None)
        
        # Eğer app.logger boşsa, config'den manuel okumayı dene (Yedek plan)
        if not LOGGER_ID:
            from config import LOGGER_ID as CONFIG_LOGGER_ID
            LOGGER_ID = CONFIG_LOGGER_ID
        
        if not LOGGER_ID:
            print("\n❌ [HATA] LOGGER_ID bulunamadı! Lütfen config.py dosyasını kontrol et.\n")
            return

        print(f"✅ Log İşlemi Başladı. Hedef Grup ID: {LOGGER_ID}")

        chat_id = message.chat.id
        
        # 1. Aktif Sesli Sohbet Sayısı
        try:
            active_calls = getattr(db, "active_calls", [])
            aktif_ses = len(active_calls) if isinstance(active_calls, list) else len(active_calls.keys())
        except Exception as e:
            print(f"⚠️ Aktif ses sayısı alınamadı: {e}")
            aktif_ses = 0

        # 2. Kanal Başlığı Güncelleme
        if aktif_ses != self.active_calls_cache:
            self.active_calls_cache = aktif_ses
            try:
                await app.set_chat_title(LOGGER_ID, f"🎧 AKTİF SES: {aktif_ses}")
            except Exception as e:
                print(f"⚠️ Log grup başlığı değişemedi (Yetki sorunu olabilir): {e}")

        # 3. Üye Sayısı
        try:
            uye_sayisi = await app.get_chat_members_count(chat_id)
        except:
            uye_sayisi = "?"

        # 4. Grup Linki
        if message.chat.username:
            grup_link = f"@{message.chat.username}"
        else:
            try:
                invite = await app.export_chat_invite_link(chat_id)
                grup_link = f"[Gizli Grup]({invite})"
            except:
                grup_link = "Bağlantı Yok"

        user = message.from_user
        mention = user.mention if user else "Bilinmiyor"
        user_id = user.id if user else 0
        
        # 5. Toplam Grup Sayısı
        try:
            toplam_grup = await db._db.chats.count_documents({})
        except:
            try:
                chats_list = await db.get_chats()
                toplam_grup = len(chats_list)
            except:
                toplam_grup = "Sayılamadı"

        # 6. LOG METNİ
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

        # 7. Log Gönderimi (HATA AYIKLAMA MODU)
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    LOGGER_ID,
                    text=logger_text,
                    disable_web_page_preview=True,
                )
                print(f"✅ LOG BAŞARIYLA GÖNDERİLDİ! -> {message.chat.title}")
            except Exception as e:
                print("\n" + "="*30)
                print(f"❌ LOG GÖNDERİLEMEDİ! İŞTE HATA SEBEBİ:")
                print(f"HATA KODU: {e}")
                print(f"Hedef ID: {LOGGER_ID}")
                print("Lütfen botun bu ID'li grupta YÖNETİCİ olduğundan emin ol.")
                print("="*30 + "\n")

    async def send_log(self, m: types.Message, chat: bool = False) -> None:
        LOGGER_ID = getattr(app, "logger", None)
        if not LOGGER_ID:
            from config import LOGGER_ID as CONFIG_LOGGER_ID
            LOGGER_ID = CONFIG_LOGGER_ID
            
        if not LOGGER_ID:
            return

        try:
            if chat:
                user = m.from_user
                text = m.lang["log_chat"].format(
                    m.chat.id, m.chat.title,
                    user.id if user else 0,
                    user.mention if user else "Anonymous",
                )
            else:
                text = m.lang["log_user"].format(
                    m.from_user.id,
                    f"@{m.from_user.username}" if m.from_user.username else "No Username",
                    m.from_user.mention,
                )
            await app.send_message(chat_id=LOGGER_ID, text=text)
        except Exception as e:
            print(f"❌ send_log Hatası: {e}")
