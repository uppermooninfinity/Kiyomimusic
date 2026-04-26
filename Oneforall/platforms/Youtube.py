import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch
from Oneforall.utils.formatters import time_to_seconds
import aiohttp
from Oneforall import LOGGER

YOUR_API_URL = "https://kartik.opusx.workers.dev/yt"
FALLBACK_API_URL = "https://kartik.opusx.workers.dev/yt"


# ---------------- SAFE SEARCH ---------------- #
async def safe_search(query, limit=1):
    try:
        results = VideosSearch(query, limit=limit)
        data = await results.next()
        if not data or "result" not in data or not data["result"]:
            return []
        return data["result"]
    except Exception:
        return []


# ---------------- API LOADER ---------------- #
async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("Oneforall.platforms.Youtube.py")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pastebin.com/raw/rLsBhAQa",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    YOUR_API_URL = (await response.text()).strip()
                    logger.info("API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
    except Exception:
        YOUR_API_URL = FALLBACK_API_URL


try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass


# ---------------- DOWNLOAD CORE ---------------- #
async def _download(link: str, media_type: str):
    global YOUR_API_URL

    if not YOUR_API_URL:
        await load_api_url()

    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    if not video_id or len(video_id) < 3:
        return None

    ext = "mp4" if media_type == "video" else "mp3"
    path = f"downloads/{video_id}.{ext}"
    os.makedirs("downloads", exist_ok=True)

    if os.path.exists(path):
        return path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": media_type}

            async with session.get(f"{YOUR_API_URL}/download", params=params) as r:
                if r.status != 200:
                    return None
                token = (await r.json()).get("download_token")

            if not token:
                return None

            stream_url = f"{YOUR_API_URL}/stream/{video_id}?type={media_type}"

            async with session.get(stream_url, headers={"X-Download-Token": token}) as f:
                if f.status != 200:
                    return None

                with open(path, "wb") as file:
                    async for chunk in f.content.iter_chunked(16384):
                        file.write(chunk)

        return path

    except Exception:
        return None


async def download_song(link: str) -> str:
    return await _download(link, "audio")


async def download_video(link: str) -> str:
    return await _download(link, "video")


# ---------------- YOUTUBE CLASS ---------------- #
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def exists(self, link: str, videoid=None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def details(self, link: str, videoid=None):
        if videoid:
            link = self.base + link

        data = await safe_search(link)
        if not data:
            return None, None, 0, None, None

        r = data[0]
        return (
            r["title"],
            r["duration"],
            int(time_to_seconds(r["duration"])) if r.get("duration") else 0,
            r["thumbnails"][0]["url"].split("?")[0],
            r["id"],
        )

    async def title(self, link: str, videoid=None):
        data = await safe_search(link)
        return data[0]["title"] if data else None

    async def duration(self, link: str, videoid=None):
        data = await safe_search(link)
        return data[0]["duration"] if data else None

    async def thumbnail(self, link: str, videoid=None):
        data = await safe_search(link)
        return data[0]["thumbnails"][0]["url"].split("?")[0] if data else None

    async def track(self, link: str, videoid=None):
        data = await safe_search(link)
        if not data:
            return None, None

        r = data[0]
        return {
            "title": r["title"],
            "link": r["link"],
            "vidid": r["id"],
            "duration_min": r["duration"],
            "thumb": r["thumbnails"][0]["url"].split("?")[0],
        }, r["id"]

    async def search(self, query: str, limit: int = 10):
        return await safe_search(query, limit)

    async def video(self, link: str, videoid=None):
        file = await download_video(link)
        return (1, file) if file else (0, "Video failed")

    async def download(self, link: str, mystic, video=None, **kwargs):
        file = await download_video(link) if video else await download_song(link)
        return (file, True) if file else (None, False)
