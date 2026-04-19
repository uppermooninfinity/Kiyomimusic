import random
import re
import string
import aiohttp

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BANNED_USERS, lyrical
from Oneforall import app

# fallback text (replace with your lang system if you have one)
_ = {
    "lyrics_1": "Give song in format: Artist - Song",
    "lyrics_2": "Searching lyrics...",
    "lyrics_3": "No lyrics found for {}",
    "lyrics_4": "Lyrics found. Click below to view.",
    "L_B_1": "View Lyrics"
}


# fetch lyrics from lyrics.ovh
async def get_lyrics(query: str):
    try:
        artist, song = query.split("-", 1)
    except ValueError:
        return None

    url = f"https://api.lyrics.ovh/v1/{artist.strip()}/{song.strip()}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data.get("lyrics")
    except Exception:
        return None


@app.on_message(filters.command(["lyrics"]) & ~BANNED_USERS)
async def lrsearch(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(_["lyrics_1"])

    query = message.text.split(None, 1)[1]
    m = await message.reply_text(_["lyrics_2"])

    lyric = await get_lyrics(query)

    if not lyric:
        return await m.edit(_["lyrics_3"].format(query))

    # clean unwanted text
    if "Embed" in lyric:
        lyric = re.sub(r"\d*Embed", "", lyric)

    ran_hash = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    lyrical[ran_hash] = lyric

    bot_username = (await app.get_me()).username

    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["L_B_1"],
                    url=f"https://t.me/{bot_username}?start=lyrics_{ran_hash}",
                ),
            ]
        ]
    )

    await m.edit(_["lyrics_4"], reply_markup=upl)
