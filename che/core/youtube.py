# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch

from che import logger
from che.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "che/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

        Path("downloads").mkdir(exist_ok=True)

    # ---------------- COOKIES ----------------
    def get_cookies(self):
        if not self.checked:
            if os.path.isdir(self.cookie_dir):
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("⚠️ YouTube cookies not found!")
            return None

        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls):
                path = f"{self.cookie_dir}/cookie_{i}.txt"
                link = "https://batbin.me/api/v2/paste/" + url.split("/")[-1]
                async with session.get(link) as resp:
                    resp.raise_for_status()
                    with open(path, "wb") as fw:
                        fw.write(await resp.read())
        logger.info("Cookies saved.")

    # ---------------- UTILS ----------------
    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    # ---------------- SEARCH ----------------
    async def search(self, query: str, m_id: int, video: bool = False):
        search = VideosSearch(query, limit=1, with_live=False)
        results = await search.next()

        if not results or not results.get("result"):
            return None

        data = results["result"][0]
        return Track(
            id=data.get("id"),
            channel_name=data.get("channel", {}).get("name", ""),
            duration=data.get("duration"),
            duration_sec=utils.to_seconds(data.get("duration")),
            message_id=m_id,
            title=data.get("title")[:90],
            thumbnail=data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
            url=data.get("link"),
            view_count=data.get("viewCount", {}).get("short"),
            video=video,
        )

    # ---------------- PLAYLIST ----------------
    async def playlist(self, limit: int, user: str, url: str, video: bool):
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                tracks.append(
                    Track(
                        id=data.get("id"),
                        channel_name=data.get("channel", {}).get("name", ""),
                        duration=data.get("duration"),
                        duration_sec=utils.to_seconds(data.get("duration")),
                        title=data.get("title")[:90],
                        thumbnail=data.get("thumbnails")[-1].get("url", "").split("?")[0],
                        url=data.get("link").split("&list=")[0],
                        user=user,
                        view_count="",
                        video=video,
                    )
                )
        except Exception as e:
            logger.warning("Playlist fetch failed: %s", e)

        return tracks

    # ---------------- DOWNLOAD ----------------
    async def download(self, video_id: str, video: bool = False):
        url = self.base + video_id
        ext = "mp4" if video else "m4a"
        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists():
            return filename

        cookie = self.get_cookies()

        ydl_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "no_warnings": True,
            "overwrites": False,
            "nocheckcertificate": True,
            "cookiefile": cookie,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            },
        }

        if video:
            ydl_opts.update({
                "format": "(bestvideo[ext=mp4][height<=720]/bestvideo)+bestaudio/best",
                "merge_output_format": "mp4",
            })
        else:
            ydl_opts.update({
                "format": "bestaudio[ext=m4a]/bestaudio/best",
            })

        def _download():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return filename
            except Exception as e:
                logger.warning("YouTube download failed: %s", e)
                return None

        return await asyncio.to_thread(_download)
