# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import time
import logging
from logging.handlers import RotatingFileHandler

# Log ayarları
logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

__version__ = "3.0.1"

from config import Config
config = Config()
config.check()
tasks = []
boot = time.time()

# Core bileşenlerin başlatılması
from che.core.bot import Bot
app = Bot()

from che.core.dir import ensure_dirs
ensure_dirs()

from che.core.userbot import Userbot
userbot = Userbot()

from che.core.mongo import MongoDB
db = MongoDB()

# DİL AYARLARI VE lang_codes EKLEMESİ
from che.core.lang import Language, lang_codes # Buraya lang_codes eklendi
lang = Language()

from che.core.telegram import Telegram
from che.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

from che.helpers import Queue
queue = Queue()

from che.core.calls import TgCall
anon = TgCall()

async def stop() -> None:
    logger.info("Stopping...")
    for task in tasks:
        task.cancel()
        try:
            await task
        except:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()
    logger.info("Stopped.\n")
