from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import re
import math
import asyncio

from Oneforall import app

# ─── 🎞️ PUT YOUR GIF FILE_ID HERE ───
GIF_ID = "AAMCBAADGQEDBzpBaeXSbXrq8paJiQABDgsc-MclFya3AAL9AwACINI8U1dYTVyrGV4KAQAHbQADOwQ"


# ─── 🧪 GET GIF FILE_ID (TEMP - REMOVE AFTER USE) ───
@app.on_message(filters.animation)
async def get_file_id(_, message: Message):
    print("GIF FILE ID:", message.animation.file_id)


# ─── 🎥 VC START ───
@app.on_message(filters.video_chat_started)
async def vc_started(_, message: Message):
    await message.reply_text(
        "<b>┃ 🎙️ ᴠᴄ ɪs ɴᴏᴡ ʟɪᴠᴇ</b>\n\n"
        "❯ ᴛʜᴇ sᴛᴀɢᴇ ɪs sᴇᴛ… ᴊᴏɪɴ ᴛʜᴇ ᴠɪʙᴇ ⚡\n"
        "❯ ᴅᴏɴ’ᴛ ᴍɪss ᴛʜᴇ ᴍᴏᴍᴇɴᴛ 🎧",
        parse_mode="html"
    )


# ─── 📴 VC END ───
@app.on_message(filters.video_chat_ended)
async def vc_ended(_, message: Message):
    await message.reply_text(
        "<b>┃ 🕊️ ᴠᴄ ᴇɴᴅᴇᴅ</b>\n\n"
        "❯ sɪʟᴇɴᴄᴇ ʀᴇᴛᴜʀɴs… 🎶\n"
        "❯ ᴜɴᴛɪʟ ɴᴇxᴛ ᴛɪᴍᴇ ⚡",
        parse_mode="html"
    )


# ─── 👥 VC INVITE WITH GIF + AUTO DELETE ───
@app.on_message(filters.video_chat_members_invited)
async def vc_invited(client: Client, message: Message):
    user = message.from_user

    text = (
        "<b>┃ 💌 ɪɴᴠɪᴛᴇ ᴀʟᴇʀᴛ</b>\n\n"
        f"❯ {user.mention} ɪs ᴄᴀʟʟɪɴɢ ʏᴏᴜ ᴛᴏ ᴛʜᴇ ᴠᴄ 🎙️\n\n"
        "❯ ᴛʜᴇ ᴠɪʙᴇ ɪs sᴇᴛ… ᴅᴏɴ’ᴛ ᴍɪss ɪᴛ ⚡\n\n"
        "<b>┃ ɪɴᴠɪᴛᴇᴅ ᴍᴇᴍʙᴇʀs</b>\n"
    )

    for member in message.video_chat_members_invited.users:
        try:
            text += f"❯ <a href='tg://user?id={member.id}'>{member.first_name}</a>\n"
        except:
            pass

    text += "\n<b>┃ 🚀 ᴊᴏɪɴ ɴᴏᴡ ᴀɴᴅ ᴍᴀᴋᴇ ɪᴛ ʟɪᴛ</b>"

    sent = await message.reply_animation(
        animation=GIF_ID,
        caption=text,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ",
                        url="https://t.me/theinfinitynetwork"
                    )
                ]
            ]
        ),
    )

    # ⏳ AUTO DELETE AFTER 15 SEC
    await asyncio.sleep(15)
    try:
        await sent.delete()
    except:
        pass


# ─── 🧮 SAFE MATH ───
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
            "<b>┃ ❗ ᴘʟᴇᴀsᴇ ɢɪᴠᴇ sᴏᴍᴇᴛʜɪɴɢ ᴛᴏ sᴇᴀʀᴄʜ</b>",
            parse_mode="html"
        )

    query = message.text.split(maxsplit=1)[1]
    msg = await message.reply_text("🔎 sᴇᴀʀᴄʜɪɴɢ...")

    async with aiohttp.ClientSession() as session:
        url = f"https://content-customsearch.googleapis.com/customsearch/v1?cx=ec8db9e1f9e41e65e&q={query}&key=YOUR_API_KEY&start=1"

        async with session.get(url) as r:
            data = await r.json()

    if not data.get("items"):
        return await msg.edit("❌ ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    result = "<b>┃ 🌐 sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs</b>\n\n"

    for item in data["items"][:5]:
        title = item["title"]
        link = item["link"]

        link = link.split("?")[0]
        link = re.sub(r"/\d", "", link)

        result += f"❯ <b>{title}</b>\n{link}\n\n"

    await msg.edit(result, disable_web_page_preview=True, parse_mode="html")
