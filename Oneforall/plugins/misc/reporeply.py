from pyrogram import filters
from pyrogram.types import Message

from Oneforall import app
from config import REPO_VID_URL
from strings import get_string


@app.on_message(filters.command("repo") & filters.private)
async def repo_reply(_, message: Message):
    strings = get_string("en")

    await message.reply_video(
        video=REPO_VID_URL,
        caption=strings["Repocaption"],
        has_spoiler=True,
    )
