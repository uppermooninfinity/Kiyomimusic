import asyncio
from yt_dlp import YoutubeDL


YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",

    # 🔥 ANDROID + WEB (ANTI BOT)
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"]
        }
    },

    # 🔥 HEADERS (IMPORTANT)
    "http_headers": {
        "User-Agent": "com.google.android.youtube/17.31.35 (Linux; Android 11)"
    },

    # 🔥 COOKIES (PUT FILE IN ROOT)
    "cookiefile": "cookies.txt",
}


class YouTubeAPI:
    def __init__(self):
        self.ydl = YoutubeDL(YTDL_OPTS)

    # ---------------- TRACK ----------------
    async def track(self, query: str):
        loop = asyncio.get_event_loop()

        try:
            data = await loop.run_in_executor(
                None,
                lambda: self.ydl.extract_info(query, download=False)
            )
        except Exception:
            # 🔥 fallback search
            data = await loop.run_in_executor(
                None,
                lambda: self.ydl.extract_info(f"ytsearch:{query}", download=False)
            )

        if "entries" in data:
            data = data["entries"][0]

        title = data.get("title", "Unknown")
        duration = data.get("duration", 0)
        link = data.get("webpage_url")
        thumb = data.get("thumbnail")

        result = {
            "title": title,
            "duration_min": self.format_duration(duration),
            "link": link,
            "thumb": thumb
        }

        return result, data.get("id")

    # ---------------- SEARCH ----------------
    async def search(self, query: str, limit: int = 5):
        loop = asyncio.get_event_loop()

        data = await loop.run_in_executor(
            None,
            lambda: self.ydl.extract_info(
                f"ytsearch{limit}:{query}",
                download=False
            )
        )

        return data.get("entries", [])

    # ---------------- DOWNLOAD / STREAM ----------------
    async def download(self, url: str, mystic=None):
        loop = asyncio.get_event_loop()

        try:
            info = await loop.run_in_executor(
                None,
                lambda: self.ydl.extract_info(url, download=False)
            )
        except Exception:
            # 🔥 retry with search fallback
            try:
                info = await loop.run_in_executor(
                    None,
                    lambda: self.ydl.extract_info(f"ytsearch:{url}", download=False)
                )
                if "entries" in info:
                    info = info["entries"][0]
            except Exception as e:
                if mystic:
                    try:
                        await mystic.edit_text(f"❌ error: {e}")
                    except:
                        pass
                return None, False

        formats = info.get("formats", [])

        # 🔥 best audio (highest bitrate)
        best_audio = max(
            (f for f in formats if f.get("acodec") != "none"),
            key=lambda x: x.get("abr", 0),
            default=None
        )

        if not best_audio:
            return None, False

        return best_audio.get("url"), True

    # ---------------- FORMAT ----------------
    def format_duration(self, seconds: int) -> str:
        if not seconds:
            return "live"

        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)

        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
