import aiohttp
import re
from py_yt import VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

API_URL = "http://45.77.174.241:9090"


class YouTubeAPI:

    def __init__(self):
        self.api = API_URL
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def search(self, query: str, limit: int = 1):
        try:
            if not query:
                return []

            results = VideosSearch(query.strip(), limit=limit)
            data = await results.next()

            if not data:
                print("SEARCH ERROR: NO DATA")
                return []

            return data.get("result", [])

        except Exception as e:
            print(f"SEARCH ERROR: {e}")
            return []

    async def get_video_id(self, query: str):
        try:

            if not query:
                return None

            if self.regex.search(query):

                if "youtu.be/" in query:
                    return query.split("youtu.be/")[1].split("?")[0]

                if "watch?v=" in query:
                    return query.split("watch?v=")[1].split("&")[0]

            results = await self.search(query)

            if not results:
                print("VIDEO ID ERROR: SEARCH EMPTY")
                return None

            return results[0]["id"]

        except Exception as e:
            print(f"VIDEO ID ERROR: {e}")
            return None

    async def get_audio(self, video_id: str):
        try:

            if not video_id:
                return None

            async with aiohttp.ClientSession() as session:

                async with session.get(
                    f"{self.api}/download",
                    params={
                        "url": video_id,
                        "type": "audio"
                    },
                    timeout=30
                ) as res:

                    if res.status != 200:
                        print(f"DOWNLOAD API ERROR: {res.status}")
                        return None

                    data = await res.json()

                    token = data.get("download_token")

                    if not token:
                        print("TOKEN NOT FOUND")
                        return None

                    stream_url = f"{self.api}/stream/{video_id}?type=audio"

                    return {
                        "id": video_id,
                        "title": "YouTube Audio",
                        "duration_min": "Unknown",
                        "duration_sec": 0,
                        "thumb": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                        "link": f"https://youtube.com/watch?v={video_id}",
                        "path": stream_url,
                        "token": token,
                    }

        except Exception as e:
            print(f"AUDIO ERROR: {e}")
            return None

    async def get_video(self, video_id: str):
        try:

            if not video_id:
                return None

            async with aiohttp.ClientSession() as session:

                async with session.get(
                    f"{self.api}/download",
                    params={
                        "url": video_id,
                        "type": "video"
                    },
                    timeout=30
                ) as res:

                    if res.status != 200:
                        print(f"VIDEO API ERROR: {res.status}")
                        return None

                    data = await res.json()

                    token = data.get("download_token")

                    if not token:
                        print("TOKEN NOT FOUND")
                        return None

                    stream_url = f"{self.api}/stream/{video_id}?type=video"

                    return {
                        "id": video_id,
                        "title": "YouTube Video",
                        "duration_min": "Unknown",
                        "duration_sec": 0,
                        "thumb": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                        "link": f"https://youtube.com/watch?v={video_id}",
                        "path": stream_url,
                        "token": token,
                    }

        except Exception as e:
            print(f"VIDEO ERROR: {e}")
            return None

    async def url(self, message: Message):
        try:

            messages = [message]

            if message.reply_to_message:
                messages.append(message.reply_to_message)

            for msg in messages:

                text = msg.text or msg.caption

                if not text:
                    continue

                urls = re.findall(
                    r"(https?://(?:www\.)?(?:youtube\.com|youtu\.be)[^\s]+)",
                    text
                )

                if urls:
                    return urls[0]

                if msg.entities:
                    for entity in msg.entities:
                        if entity.type == MessageEntityType.URL:
                            return text[
                                entity.offset: entity.offset + entity.length
                            ]

                if msg.caption_entities:
                    for entity in msg.caption_entities:
                        if entity.type == MessageEntityType.TEXT_LINK:
                            return entity.url

            return None

        except Exception as e:
            print(f"URL ERROR: {e}")
            return None

    async def exists(self, link: str, videoid: bool = None):
        try:

            if not link:
                return False

            return bool(re.search(self.regex, link))

        except Exception as e:
            print(f"EXISTS ERROR: {e}")
            return False

    async def title(self, link: str, videoid: bool = None):
        try:

            vid = await self.get_video_id(link)

            if not vid:
                return "Unknown Title"

            results = VideosSearch(vid, limit=1)
            data = await results.next()

            return data["result"][0]["title"]

        except Exception as e:
            print(f"TITLE ERROR: {e}")
            return "Unknown Title"

    async def duration(self, link: str, videoid: bool = None):
        try:

            vid = await self.get_video_id(link)

            if not vid:
                return "Unknown"

            results = VideosSearch(vid, limit=1)
            data = await results.next()

            return data["result"][0]["duration"]

        except Exception as e:
            print(f"DURATION ERROR: {e}")
            return "Unknown"

    async def thumbnail(self, link: str, videoid: bool = None):
        try:

            vid = await self.get_video_id(link)

            if not vid:
                return None

            return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

        except Exception as e:
            print(f"THUMB ERROR: {e}")
            return None

    async def play_audio(self, query: str):
        try:

            video_id = await self.get_video_id(query)

            if not video_id:
                print("PLAY AUDIO ERROR: VIDEO ID NOT FOUND")
                return None

            return await self.get_audio(video_id)

        except Exception as e:
            print(f"PLAY AUDIO ERROR: {e}")
            return None

    async def play_video(self, query: str):
        try:

            video_id = await self.get_video_id(query)

            if not video_id:
                print("PLAY VIDEO ERROR: VIDEO ID NOT FOUND")
                return None

            return await self.get_video(video_id)

        except Exception as e:
            print(f"PLAY VIDEO ERROR: {e}")
            return None

    async def track(self, query: str, videoid: bool = False):
        try:

            if videoid:
                vid = query
            else:
                vid = await self.get_video_id(query)

            if not vid:
                print("TRACK ERROR: VIDEO ID NOT FOUND")
                return None, None

            results = VideosSearch(vid, limit=1)
            data = await results.next()

            if not data:
                print("TRACK ERROR: NO DATA")
                return None, None

            result = data.get("result")

            if not result:
                print("TRACK ERROR: EMPTY RESULT")
                return None, None

            result = result[0]

            details = {
                "title": result.get("title", "Unknown"),
                "duration_min": result.get("duration", "Unknown"),
                "thumb": result["thumbnails"][0]["url"].split("?")[0]
                if result.get("thumbnails")
                else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "link": f"https://youtube.com/watch?v={vid}",
                "path": f"{self.api}/stream/{vid}?type=audio",
                "id": vid,
            }

            print(f"TRACK SUCCESS: {details}")

            return details, vid

        except Exception as e:
            print(f"TRACK ERROR: {e}")
            return None, None


YouTube = YouTubeAPI()
