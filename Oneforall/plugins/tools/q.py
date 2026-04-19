from io import BytesIO
import asyncio
import logging

from httpx import AsyncClient, Timeout
from pyrogram import filters
from pyrogram.types import Message, InputSticker

from Oneforall import app

fetch = AsyncClient(
    http2=True,
    verify=False,
    headers={
        "Accept-Language": "id-ID",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
    timeout=Timeout(20),
)


class QuotlyException(Exception):
    pass


async def get_message_sender_id(ctx: Message):
    if ctx.forward_date:
        if ctx.forward_sender_name:
            return 1
        elif ctx.forward_from:
            return ctx.forward_from.id
        elif ctx.forward_from_chat:
            return ctx.forward_from_chat.id
        else:
            return 1
    elif ctx.from_user:
        return ctx.from_user.id
    elif ctx.sender_chat:
        return ctx.sender_chat.id
    else:
        return 1


async def get_message_sender_name(ctx: Message):
    if ctx.forward_date:
        if ctx.forward_sender_name:
            return ctx.forward_sender_name
        elif ctx.forward_from:
            return (
                f"{ctx.forward_from.first_name} {ctx.forward_from.last_name}"
                if ctx.forward_from.last_name
                else ctx.forward_from.first_name
            )
        elif ctx.forward_from_chat:
            return ctx.forward_from_chat.title
        else:
            return ""
    elif ctx.from_user:
        if ctx.from_user.last_name:
            return f"{ctx.from_user.first_name} {ctx.from_user.last_name}"
        else:
            return ctx.from_user.first_name
    elif ctx.sender_chat:
        return ctx.sender_chat.title
    else:
        return ""


async def get_message_sender_username(ctx: Message):
    if ctx.forward_date:
        return ""
    elif ctx.from_user and ctx.from_user.username:
        return ctx.from_user.username
    return ""


async def get_message_sender_photo(ctx: Message):
    return ""


async def get_text_or_caption(ctx: Message):
    return ctx.text or ctx.caption or ""


async def pyrogram_to_quotly(messages, is_reply):
    if not isinstance(messages, list):
        messages = [messages]

    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": "#1b1429",
        "messages": [],
    }

    for message in messages:
        the_message_dict_to_append = {}
        the_message_dict_to_append["chatId"] = await get_message_sender_id(message)
        the_message_dict_to_append["text"] = await get_text_or_caption(message)
        the_message_dict_to_append["avatar"] = True
        the_message_dict_to_append["from"] = {}
        the_message_dict_to_append["from"]["id"] = await get_message_sender_id(message)
        the_message_dict_to_append["from"]["name"] = await get_message_sender_name(message)
        the_message_dict_to_append["from"]["username"] = await get_message_sender_username(message)
        the_message_dict_to_append["from"]["type"] = message.chat.type.name.lower()
        the_message_dict_to_append["from"]["photo"] = await get_message_sender_photo(message)

        if message.reply_to_message and is_reply:
            the_message_dict_to_append["replyMessage"] = {
                "name": await get_message_sender_name(message.reply_to_message),
                "text": await get_text_or_caption(message.reply_to_message),
                "chatId": await get_message_sender_id(message.reply_to_message),
            }
        else:
            the_message_dict_to_append["replyMessage"] = {}

        payload["messages"].append(the_message_dict_to_append)

    r = await fetch.post("https://bot.lyo.su/quote/generate.png", json=payload)
    if not r.is_error:
        return r.read()
    else:
        raise QuotlyException(r.json())


def isArgInt(txt) -> list:
    try:
        return [True, int(txt)]
    except ValueError:
        return [False, 0]


@app.on_message(filters.command(["q", "r"]) & filters.reply)
async def msg_quotly_cmd(self: app, ctx: Message):
    ww = await ctx.reply_text("wait...")

    is_reply = ctx.command[0].endswith("r")

    try:
        messages_one = await self.get_messages(
            chat_id=ctx.chat.id,
            message_ids=ctx.reply_to_message.id,
            replies=-1
        )
        messages = [messages_one]

        make_quotly = await pyrogram_to_quotly(messages, is_reply=is_reply)
        bio_sticker = BytesIO(make_quotly)
        bio_sticker.name = "quote.webp"

        await ww.delete()
        await ctx.reply_sticker(bio_sticker)

        user_mention = ctx.from_user.mention if ctx.from_user else "User"
        note = await ctx.reply_text(
            f"<blockquote>🔥 Hey {user_mention}, fast use /kang and make this sticker a part of your stickerpack</blockquote>"
        )

        await asyncio.sleep(15)
        await note.delete()

    except Exception as e:
        await ww.delete()
        return await ctx.reply_text(f"ERROR: {e}")


@app.on_message(filters.command("kang") & filters.reply)
async def kang_sticker(client, message: Message):
    if not message.reply_to_message.sticker:
        return await message.reply_text("Reply to a sticker.")

    sticker = message.reply_to_message.sticker
    user_id = message.from_user.id
    bot_username = (await client.get_me()).username

    pack_name = f"a{user_id}_by_{bot_username}"
    pack_title = f"{message.from_user.first_name}'s Pack"

    emoji = sticker.emoji or "🙂"

    try:
        input_sticker = InputSticker(
            sticker=sticker.file_id,
            emoji_list=[emoji],
        )

        try:
            await client.add_sticker_to_set(
                user_id=user_id,
                name=pack_name,
                stickers=[input_sticker],
            )
            await message.reply_text(f"https://t.me/addstickers/{pack_name}")

        except Exception:
            await client.create_new_sticker_set(
                user_id=user_id,
                name=pack_name,
                title=pack_title,
                stickers=[input_sticker],
            )
            await message.reply_text(f"https://t.me/addstickers/{pack_name}")

    except Exception as e:
        logging.exception(e)
        await message.reply_text("kang failed")
