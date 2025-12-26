import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from che import config
from che.helpers import Track

# Dosya yolunu çalışma dizinine göre ayarla
BASE_DIR = os.getcwd()

class Thumbnail:
    def __init__(self):
        self.rect = (914, 514)
        self.fill = (255, 255, 255)
        self.mask = Image.new("L", self.rect, 0)
        
        # Font yollarını güvenli hale getir
        font1_path = os.path.join(BASE_DIR, "anony", "helpers", "Raleway-Bold.ttf")
        font2_path = os.path.join(BASE_DIR, "anony", "helpers", "Inter-Light.ttf")

        # Fontları yükle, eğer dosya yoksa varsayılan sistem fontunu kullan (Hata önleyici)
        try:
            self.font1 = ImageFont.truetype(font1_path, 30)
            self.font2 = ImageFont.truetype(font2_path, 30)
        except OSError:
            print(f"UYARI: Font dosyaları {font1_path} yolunda bulunamadı. Varsayılan font kullanılıyor.")
            self.font1 = ImageFont.load_default()
            self.font2 = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(output_path, "wb") as f:
                        f.write(await resp.read())
                    return output_path
                return None

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            # Cache klasörünü kontrol et yoksa oluştur
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            
            if os.path.exists(output):
                return output

            downloaded = await self.save_thumb(temp, song.thumbnail)
            if not downloaded:
                return config.DEFAULT_THUMB

            thumb = Image.open(temp).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            blur = thumb.filter(ImageFilter.GaussianBlur(25))
            image = ImageEnhance.Brightness(blur).enhance(.40)

            _rect = ImageOps.fit(thumb, self.rect, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            # Maske üzerine yuvarlatılmış köşe çiz
            draw_mask = ImageDraw.Draw(self.mask)
            draw_mask.rounded_rectangle((0, 0, self.rect[0], self.rect[1]), radius=15, fill=255)
            
            _rect.putalpha(self.mask)
            image.paste(_rect, (183, 30), _rect)

            draw = ImageDraw.Draw(image)
            
            # Yazıları ekle (Kesilme ihtimaline karşı [:25] gibi limitler güvenli)
            draw.text((50, 560), f"{song.channel_name[:25]} | {song.view_count}", font=self.font2, fill=self.fill)
            draw.text((50, 600), song.title[:50], font=self.font1, fill=self.fill)
            draw.text((40, 650), "0:01", font=self.font1)
            
            # İlerleme çubuğu
            draw.line([(140, 670), (1160, 670)], fill=self.fill, width=5)
            draw.text((1185, 650), song.duration, font=self.font1, fill=self.fill)

            image.save(output)
            
            if os.path.exists(temp):
                os.remove(temp)
                
            return output
        except Exception as e:
            print(f"Thumbnail Hatası: {e}")
            return config.DEFAULT_THUMB
