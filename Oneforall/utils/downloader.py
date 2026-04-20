import os
import asyncio
import yt_dlp

# ─── Ensure download folder ───
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# ─── PRIMARY OPTIONS (FAST + RELIABLE) ───
BASE_OPTS = {
    "format": "bestaudio/best",   # fallback-safe
    "outtmpl": "downloads/%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "geo_bypass": True,
    "nocheckcertificate": True,

    # 🔁 retry system
    "retries": 5,
    "fragment_retries": 5,
    "skip_unavailable_fragments": True,

    # ⚡ speed
    "concurrent_fragment_downloads": 8,

    # 🚀 aria2 (BIG speed boost)
    "external_downloader": "aria2c",
    "external_downloader_args": [
        "-x", "16",   # connections
        "-k", "1M",   # chunk size
        "--summary-interval=0"
    ],

    # 🎯 extractor tuning
    "extractor_args": {
        "youtube": {
            "skip": ["dash"],   # avoid slow dash
        }
    },
}


# ─── FALLBACK OPTIONS (SECOND ATTEMPT) ───
FALLBACK_OPTS = {
    **BASE_OPTS,
    "format": "best",   # if audio extraction fails, take best media
}


# ─── MAIN DOWNLOAD FUNCTION ───
async def download(url: str, progress_hook=None) -> str:
    loop = asyncio.get_event_loop()

    def run(opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            if progress_hook:
                ydl.add_progress_hook(progress_hook)

            info = ydl.extract_info(url, download=True)

            return os.path.join(
                "downloads",
                f"{info['id']}.{info['ext']}"
            )

    # ─── TRY PRIMARY ───
    try:
        return await loop.run_in_executor(None, lambda: run(BASE_OPTS))
    except Exception as e:
        print("⚠️ Primary failed:", e)

    # ─── TRY FALLBACK ───
    try:
        return await loop.run_in_executor(None, lambda: run(FALLBACK_OPTS))
    except Exception as e:
        print("❌ Fallback failed:", e)
        return None


# ─── OPTIONAL PROGRESS HOOK ───
def progress_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "")
        eta = d.get("_eta_str", "")

        print(f"⬇️ {percent} | ⚡ {speed} | ⏳ {eta}")

    elif d["status"] == "finished":
        print("✅ Download completed")
