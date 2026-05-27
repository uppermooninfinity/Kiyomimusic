import requests
from pyrogram import filters
from pyrogram.types import Message

from config import OWNER_ID, BOT_TOKEN
from Oneforall import app


@app.on_message(filters.command("setpfp") & filters.private)
async def set_pfp(client, message: Message):

    if message.from_user.id != OWNER_ID:
        return await message.reply_text("not authorized.")

    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("reply to a photo.")

    msg = await message.reply_text("updating bot pfp...")

    try:
        photo_path = await message.reply_to_message.download()

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setUserProfilePhotos"

        with open(photo_path, "rb") as photo:
            response = requests.post(
                url,
                files={"photo": photo}
            )

        await msg.edit(response.text)

    except Exception as e:
        await msg.edit(str(e))
