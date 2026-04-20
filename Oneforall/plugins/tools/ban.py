

import html
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from Oneforall import app


async def is_admin(chat_id, user_id):
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False



async def extract_user(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id, None

    if len(message.command) < 2:
        return None, None

    user = message.command[1]
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else None

    if user.isdigit():
        return int(user), reason

    try:
        user_obj = await app.get_users(user)
        return user_obj.id, reason
    except:
        return None, None

@app.on_message(filters.command(["ban", "sban"]) & filters.group)
async def ban_user(client, message: Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("ᴀᴅᴍɪɴs ᴏɴʟʏ")

    user_id, reason = await extract_user(message)

    if not user_id:
        return await message.reply_text("ɪ ᴅᴏᴜʙᴛ ᴛʜᴀᴛ's ᴀ ᴜsᴇʀ.")

    if user_id == (await client.get_me()).id:
        return await message.reply_text("ᴏʜ ʏᴇᴀʜ, ʙᴀɴ ᴍʏsᴇʟғ, ɴᴏᴏʙ!")

    try:
        member = await client.get_users(user_id)
    except:
        return await message.reply_text("ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜɪs ᴜsᴇʀ.")

    silent = message.command[0] == "sban"

    try:
        await client.ban_chat_member(message.chat.id, user_id)

        if silent:
            await message.delete()
            if message.reply_to_message:
                await message.reply_to_message.delete()
            return

        reply = (
            f"<code>❕</code><b>ʙᴀɴ ᴇᴠᴇɴᴛ</b>\n"
            f"<code> </code><b>•  ʙᴀɴɴᴇᴅ ʙʏ:</b> {message.from_user.mention}\n"
            f"<code> </code><b>•  ᴜsᴇʀ:</b> {member.mention}"
        )

        if reason:
            reply += f"\n<code> </code><b>•  ʀᴇᴀsᴏɴ:</b> {html.escape(reason)}"

        await message.reply_text(reply)

    except Exception as e:
        await message.reply_text("ᴜʜᴍ ...ᴛʜᴀᴛ ᴅɪᴅɴ'ᴛ ᴡᴏʀᴋ ..")

@app.on_message(filters.command("tban") & filters.group)
async def temp_ban(client, message: Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("ᴀᴅᴍɪɴs ᴏɴʟʏ")

    user_id, reason = await extract_user(message)

    if not user_id:
        return await message.reply_text("ɪ ᴅᴏᴜʙᴛ ᴛʜᴀᴛ's ᴀ ᴜsᴇʀ.")

    if not reason:
        return await message.reply_text("ɴᴏ ᴛɪᴍᴇ ɢɪᴠᴇɴ.")

    time_map = {"m": 60, "h": 3600, "d": 86400}

    try:
        time_val = reason.split()[0]
        unit = time_val[-1]
        value = int(time_val[:-1])
        seconds = value * time_map[unit]
    except:
        return await message.reply_text("ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ.")

    try:
        await client.ban_chat_member(
            message.chat.id,
            user_id,
            until_date=int(seconds + message.date.timestamp())
        )

        await message.reply_text(
            f"ʙᴀɴɴᴇᴅ! ᴜsᴇʀ ɪs ʙᴀɴɴᴇᴅ ғᴏʀ {time_val}."
        )

    except:
        await message.reply_text("ᴄᴀɴ'ᴛ ʙᴀɴ.")



@app.on_message(filters.command("kick") & filters.group)
async def kick_user(client, message: Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("ᴀᴅᴍɪɴs ᴏɴʟʏ")

    user_id, _ = await extract_user(message)

    if not user_id:
        return await message.reply_text("ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ.")

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await client.unban_chat_member(message.chat.id, user_id)

        await message.reply_text("ᴋɪᴄᴋᴇᴅ!")

    except:
        await message.reply_text("ᴄᴀɴ'ᴛ ᴋɪᴄᴋ.")


@app.on_message(filters.command("unban") & filters.group)
async def unban_user(client, message: Message):

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("ᴀᴅᴍɪɴs ᴏɴʟʏ")

    user_id, _ = await extract_user(message)

    if not user_id:
        return await message.reply_text("ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ.")

    try:
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text("ᴜɴʙᴀɴɴᴇᴅ!")

    except:
        await message.reply_text("ᴄᴀɴ'ᴛ ᴜɴʙᴀɴ.")

@app.on_message(filters.command("kickme") & filters.group)
async def kickme(client, message: Message):

    if await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴋɪᴄᴋ ᴀɴ ᴀᴅᴍɪɴ.")

    try:
        await client.ban_chat_member(message.chat.id, message.from_user.id)
        await client.unban_chat_member(message.chat.id, message.from_user.id)

        await message.reply_text("*ᴋɪᴄᴋs ʏᴏᴜ*")

    except:
        await message.reply_text("ᴇʀʀᴏʀ.")
