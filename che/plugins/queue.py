from pyrogram import filters, types
from che import app, config, db, lang, queue
from che.helpers import Track, buttons

@app.on_message(filters.command(["queue", "kuyruk", "playing"]) & filters.group & ~app.bl_users)
@lang.language()
async def _queue_func(_, m: types.Message):
    # O an sesli sohbet aktif mi kontrolü
    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    # İşlem başladığına dair ön mesaj
    _reply = await m.reply_text(m.lang["queue_fetching"])
    
    # Kuyruğu al
    _queue = queue.get_queue(m.chat.id)
    if not _queue:
        return await _reply.edit_text("⚠️ **Kuyruk şu an boş.**")

    # Şu an çalan medya bilgisi
    _media = _queue[0]

    # Metin Oluşturma: Şu an çalan
    _text = m.lang["queue_curr"].format(
        _media.url,
        _media.title,
        _media.duration,
        _media.user,
    )

    # Alt Bilgi: Kuyruk listesi
    _queue_list = _queue[1:]
    if _queue_list:
        _text += "\n\n<b>📋 Sıradaki Şarkılar</b>"
        _text += "<blockquote expandable>"
        for i, media in enumerate(_queue_list, start=1):
            if i == 15: # İlk 15 şarkıyı göster
                break
            # Temiz bir liste görünümü
            _text += f"\n<b>{i}.</b> {media.title[:35]}... (👤 {media.user})"
        _text += "</blockquote>"
        
        # Eğer kuyruk 15'ten fazlaysa toplam sayıyı belirt
        if len(_queue_list) > 15:
            _text += f"\n\n✨ <i>Toplamda {len(_queue_list)} şarkı sırada bekliyor.</i>"

    # Çalma durumu kontrolü (Duraklatıldı mı yoksa oynatılıyor mu?)
    _playing = await db.playing(m.chat.id)
    
    # Butonları oluştur
    _markup = buttons.queue_markup(
        m.chat.id,
        m.lang["playing"] if _playing else m.lang["paused"],
        _playing,
    )

    # Mesajı metin ve butonlarla güncelle
    await _reply.edit_text(
        text=_text,
        reply_markup=_markup,
        disable_web_page_preview=True # Link önizlemesini kapatarak daha temiz görünüm sağlar
    )
