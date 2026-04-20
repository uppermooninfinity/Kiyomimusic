from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import re
import math
import asyncio
import os

from Oneforall import app


# ─── 🎥 CATBOX VIDEO LINK ───
CATBOX_URL = "https://graph.org/file/9f9cb0ab87e4f7b6c061a-3544c3bdcf44adbe03.mp4"
VIDEO_PATH = "vc_video.mp4"


# ─── 🎙️ VC START ───
@app.on_message(filters.video_chat_started)
async def vc_started(_, message: Message):
    await message.reply_text(
        "<b>┃ 🎙️ ᴠᴄ ɪs ɴᴏᴡ ʟɪᴠᴇ</b>\n\n"
        "❯ sᴛᴀɢᴇ ʀᴇᴀᴅʏ ⚡\n"
        "❯ ᴊᴏɪɴ ᴛʜᴇ ᴠɪʙᴇ 🎧",
        parse_mode="html"
    )


# ─── 📴 VC END ───
@app.on_message(filters.video_chat_ended)
async def vc_ended(_, message: Message):
    await message.reply_text(
        "<b>┃ 🕊️ ᴠᴄ ᴇɴᴅᴇᴅ</b>\n\n"
        "❯ sɪʟᴇɴᴄᴇ ʀᴇᴛᴜʀɴs 🎶\n"
        "❯ sᴇᴇ ʏᴏᴜ sᴏᴏɴ ⚡",
        parse_mode="html"
    )


# ─── 👥 VC INVITE (CATBOX VIDEO) ───
@app.on_message(filters.video_chat_members_invited)
async def vc_invited(_, message: Message):
    user = message.from_user

    text = (
        "<b>┃ 💌 ɪɴᴠɪᴛᴇ ᴀʟᴇʀᴛ</b>\n\n"
        f"❯ {user.mention} ɪɴᴠɪᴛᴇᴅ ʏᴏᴜ 🎙️\n\n"
        "<b>┃ ᴊᴏɪɴ ɴᴏᴡ ⚡</b>"
    )

    # ─── DOWNLOAD CATBOX VIDEO ───
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CATBOX_URL) as resp:
                if resp.status == 200:
                    with open(VIDEO_PATH, "wb") as f:
                        f.write(await resp.read())
    except:
        return await message.reply_text("❌ ᴠɪᴅᴇᴏ ʟᴏᴀᴅ ғᴀɪʟᴇᴅ")

    sent = await message.reply_video(
        video=VIDEO_PATH,
        caption=text,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/theinfinitynetwork")]]
        ),
    )

    await asyncio.sleep(15)

    try:
        await sent.delete()
    except:
        pass

    # cleanup
    if os.path.exists(VIDEO_PATH):
        os.remove(VIDEO_PATH)


# ─── 🧮 MATH ───
@app.on_message(filters.command("math"))
async def calculate_math(_, message: Message):
    try:
        expression = message.text.split(maxsplit=1)[1]
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
        result = eval(expression, {"__builtins__": {}}, allowed_names)

        await message.reply_text(
            f"<b>┃ 🧠 ʀᴇsᴜʟᴛ</b>\n\n❯ <code>{result}</code>",
            parse_mode="html"
        )
    except:
        await message.reply_text(
            "<b>┃ ⚠️ ɪɴᴠᴀʟɪᴅ ᴇxᴘʀᴇssɪᴏɴ</b>",
            parse_mode="html"
        )


# ─── 🔍 SEARCH ───
@app.on_message(filters.command("spg", prefixes=["/", "!", "."]))
async def search(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>┃ ❗ ɢɪᴠᴇ sᴇᴀʀᴄʜ ǫᴜᴇʀʏ</b>",
            parse_mode="html"
        )

    query = message.text.split(maxsplit=1)[1]
    msg = await message.reply_text("🔎 sᴇᴀʀᴄʜɪɴɢ...")

    async with aiohttp.ClientSession() as session:
        url = f"https://content-customsearch.googleapis.com/customsearch/v1?cx=ec8db9e1f9e41e65e&q={query}&key=YOUR_API_KEY"

        async with session.get(url) as r:
            data = await r.json()

    if not data.get("items"):
        return await msg.edit("❌ ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    result = "<b>┃ 🌐 sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs</b>\n\n"

    for item in data["items"][:5]:
        title = item["title"]
        link = item["link"].split("?")[0]
        link = re.sub(r"/\d", "", link)
        result += f"❯ <b>{title}</b>\n{link}\n\n"

    await msg.edit(result, disable_web_page_preview=True, parse_mode="html")
