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

    # 🔥 FAST MODE (ANDROID CLIENT)
    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    },
}


class YouTubeAPI:
    def __init__(self):
        self.ydl = YoutubeDL(YTDL_OPTS)

    # ---------------- TRACK (PLAY COMMAND) ----------------
    async def track(self, query: str):
        loop = asyncio.get_event_loop()

        data = await loop.run_in_executor(
            None,
            lambda: self.ydl.extract_info(query, download=False)
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

    # ---------------- SEARCH (AUTOPLAY USE) ----------------
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

    # ---------------- GET DIRECT STREAM URL ----------------
    async def download(self, url: str, mystic=None):
        loop = asyncio.get_event_loop()

        try:
            info = await loop.run_in_executor(
                None,
                lambda: self.ydl.extract_info(url, download=False)
            )

            formats = info.get("formats", [])

            best_audio = None

            for f in formats:
                if f.get("acodec") != "none":
                    best_audio = f
                    break

            if not best_audio:
                return None, False

            audio_url = best_audio.get("url")

            return audio_url, True

        except Exception as e:
            if mystic:
                try:
                    await mystic.edit_text(f"❌ error: {e}")
                except:
                    pass
            return None, False

    # ---------------- FORMAT DURATION ----------------
    def format_duration(self, seconds: int) -> str:
        if not seconds:
            return "live"

        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)

        if h:
            return f"{h}:{m:02d}:{s:02d}"
        else:
            return f"{m}:{s:02d}"
