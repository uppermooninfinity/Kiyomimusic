from pyrogram.enums import ParseMode

from Oneforall import app
from Oneforall.utils.database import is_on_off
from config import LOGGER_ID

LOGGER_PIC = "https://graph.org/file/63b3df811a74a74849d45-f46859bfc348595942.jpg"  # put your image link here


async def play_logs(message, streamtype):
    if await is_on_off(2):

        query = (
            message.text.split(None, 1)[1]
            if len(message.text.split()) > 1
            else "Unknown"
        )

        logger_text = f"""
<b>➻ 𝛂 ηєᴡ ᴧᴄᴛɪᴠɪᴛʏ ɪѕ ᴅєᴛєᴄᴛєᴅ 🎵</b>

<b>⌬ ᴄʜᴧᴛ</b>
<b>• ɴᴧϻє :</b> {message.chat.title}
<b>• ɪᴅ :</b> <code>{message.chat.id}</code>
<b>• ᴜѕєʀɴᴧϻє :</b> @{message.chat.username}

<b>⌬ ᴜѕєʀ</b>
<b>• ɴᴧϻє :</b> {message.from_user.mention}
<b>• ɪᴅ :</b> <code>{message.from_user.id}</code>
<b>• ᴜѕєʀɴᴧϻє :</b> @{message.from_user.username}

<b>⌬ ѕᴛʀєᴧϻ</b>
<b>• ᴛʏᴘє :</b> {streamtype}
<b>• ǫᴜєʀʏ :</b> <code>{query}</code>

<b>⌬ ʙʏ :</b> {app.mention}
"""

        if message.chat.id != LOGGER_ID:
            try:
                await app.send_photo(
                    chat_id=LOGGER_ID,
                    photo=LOGGER_PIC,
                    caption=logger_text,
                    parse_mode=ParseMode.HTML,
                )
            except:
                pass

        return
