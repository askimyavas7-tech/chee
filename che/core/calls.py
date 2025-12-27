import time
from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported)
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from che import app, config, db, lang, logger, queue, userbot, yt
from che.helpers import Media, Track, buttons

class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        return await client.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        return await client.resume(chat_id)

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        try:
            queue.clear(chat_id)
            await db.remove_call(chat_id)
            await db.set_loop(chat_id, 0)  # Durdurunca döngüyü sıfırla
        except:
            pass

        try:
            await client.leave_call(chat_id, close=False)
        except:
            pass

    async def loop(self, chat_id: int, count: int) -> None:
        """Döngü sayısını ayarlar."""
        await db.set_loop(chat_id, count)

    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang(chat_id)
        
        if not media.file_path:
            # Dosya yolu yoksa hata ver ve sonrakine geç
            if message:
                await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            return await self.play_next(chat_id)

        # Video flag ayarı
        video_flags = types.MediaStream.Flags.IGNORE
        if media.video:
            video_flags = types.MediaStream.Flags.AUTO_DETECT

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=video_flags,
            ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 0 else None,
        )

        try:
            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )
            
            # Zamanlayıcıları ayarla
            media.start_time = time.time()
            if not seek_time:
                media.played_prefix = 0
                media.time = 1
                await db.add_call(chat_id)
                
                # Mesaj formatı
                text = _lang["play_media"].format(
                    media.url,
                    media.title,
                    media.duration,
                    media.user,
                )
                keyboard = buttons.controls(chat_id)
                
                # Mesajı gönderme veya düzenleme
                try:
                    if message:
                        await message.edit_text(
                            text=text,
                            reply_markup=keyboard,
                        )
                    else:
                        msg = await app.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard,
                        )
                        media.message_id = msg.id
                except MessageIdInvalid:
                    # Mesaj silinmişse yenisini at
                    msg = await app.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=keyboard,
                    )
                    media.message_id = msg.id
                except Exception:
                    pass
            else:
                # Seek yapılıyorsa played_prefix güncellenir
                media.played_prefix = seek_time

        except FileNotFoundError:
            if message:
                await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            if message:
                await message.edit_text(_lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            if message:
                await message.edit_text(_lang["error_no_audio"])
            await self.play_next(chat_id)
        except (ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            if message:
                await message.edit_text(_lang["error_tg_server"])
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            if message:
                await message.edit_text(_lang["error_rtmp"])

    async def seek(self, chat_id: int, seconds: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        if not media:
            return

        try:
            msg = await app.get_messages(chat_id, media.message_id)
        except:
            _lang = await lang.get_lang(chat_id)
            msg = await app.send_message(chat_id, _lang["processing"])

        # Süre hesaplaması
        current_played = getattr(media, "played_prefix", 0) + (time.time() - getattr(media, "start_time", time.time()))
        
        seek_to = int(current_played + seconds)
        if seek_to < 0:
            seek_to = 0
            
        await self.play_media(chat_id, msg, media, seek_time=seek_to)

    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        if not media:
            return
            
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        await self.play_media(chat_id, msg, media)

    async def play_next(self, chat_id: int) -> None:
        """Sıradaki şarkıya geçiş ve DÖNGÜ kontrolü."""
        
        # --- DÖNGÜ (LOOP) MANTIĞI BAŞLANGIÇ ---
        loop_count = await db.get_loop(chat_id)
        
        if loop_count > 0:
            await db.decrease_loop(chat_id)
            media = queue.get_current(chat_id) # Mevcut medyayı al
            
            if media:
                _lang = await lang.get_lang(chat_id)
                # Kullanıcıya döngüde olduğunu bildiren mesaj (İsteğe bağlı metin düzenlenebilir)
                loop_text = _lang.get("play_next", "🔄 Şarkı tekrarlanıyor...") 
                msg = await app.send_message(chat_id=chat_id, text=loop_text)
                media.message_id = msg.id
                return await self.play_media(chat_id, msg, media)
        # --- DÖNGÜ MANTIĞI BİTİŞ ---

        # Döngü yoksa sıradaki şarkıya geç
        media = queue.get_next(chat_id)
        
        try:
            # Eski mesajı sil
            old_media = queue.get_current(chat_id) # Temizlik için kontrol
            if old_media and old_media.message_id:
                await app.delete_messages(
                    chat_id=chat_id,
                    message_ids=old_media.message_id,
                    revoke=True,
                )
        except:
            pass

        if not media:
            return await self.stop(chat_id)

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
        
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.stop(chat_id)
                return await msg.edit_text(
                    _lang["error_no_file"].format(config.SUPPORT_CHAT)
                )

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)

    async def ping(self) -> float:
        if not self.clients:
            return 0.0
        pings = [client.ping for client in self.clients]
        if not pings:
            return 0.0
        return round(sum(pings) / len(pings), 2)

    async def decorators(self, client: PyTgCalls) -> None:
        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    # Şarkı bittiğinde play_next çalışır (Döngü burada devreye girer)
                    await self.play_next(update.chat_id)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)

    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")
