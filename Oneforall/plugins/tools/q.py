from io import BytesIO
import asyncio
import logging
import os
import shutil
import tempfile
import traceback

from httpx import AsyncClient, Timeout
from pyrogram import filters, raw
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import StickersetInvalid, StickersTooMuch, FloodWait, RPCError

from Oneforall import app


BOT = None


async def get_bot_username(client):
    global BOT
    if not BOT:
        me = await client.get_me()
        BOT = me.username.lower()
    return BOT


async def build_pack_name(client, user_id, index=0):
    bot = await get_bot_username(client)
    return f"user{user_id}_pack{index}_by_{bot}"


fetch = AsyncClient(
    http2=True,
    verify=False,
    timeout=Timeout(20),
)


class QuotlyException(Exception):
    pass


async def get_text_or_caption(ctx: Message):
    return ctx.text or ctx.caption or ""


async def pyrogram_to_quotly(messages):
    if not isinstance(messages, list):
        messages = [messages]

    payload = {
        "type": "quote",
        "format": "png",
        "messages": [],
    }

    for message in messages:
        payload["messages"].append({
            "chatId": message.from_user.id if message.from_user else 0,
            "text": await get_text_or_caption(message),
            "from": {
                "id": message.from_user.id if message.from_user else 0,
                "name": message.from_user.first_name if message.from_user else "User",
            },
        })

    r = await fetch.post("https://bot.lyo.su/quote/generate.png", json=payload)
    if not r.is_error:
        return r.read()
    raise QuotlyException("Quote API failed")


@app.on_message(filters.command(["q", "r"]) & filters.reply)
async def quote_handler(client, message: Message):
    msg = await message.reply_text("processing...")

    try:
        m = await client.get_messages(message.chat.id, message.reply_to_message.id)
        data = await pyrogram_to_quotly([m])

        bio = BytesIO(data)
        bio.name = "quote.webp"

        await msg.delete()
        await message.reply_sticker(bio)

        note = await message.reply_text(
            f"<blockquote>🔥 Hey {message.from_user.mention}, fast use /kang and make this sticker part of your pack</blockquote>"
        )

        await asyncio.sleep(15)
        await note.delete()

    except Exception as e:
        await msg.edit(f"ERROR: {e}")


@app.on_message(filters.command("kang") & filters.reply)
async def kang(client, message: Message):
    notify = await message.reply_text("processing...")
    tmp_dir = tempfile.mkdtemp()

    try:
        reply = message.reply_to_message

        if not reply.sticker:
            return await notify.edit("reply to a sticker only")

        file_path = await reply.download(os.path.join(tmp_dir, "sticker.webp"))

        uid = message.from_user.id
        uname = message.from_user.first_name

        idx = 0
        while True:
            short = await build_pack_name(client, uid, idx)
            try:
                sset = await client.invoke(
                    raw.functions.messages.GetStickerSet(
                        stickerset=raw.types.InputStickerSetShortName(short_name=short),
                        hash=0
                    )
                )
                if len(sset.documents) >= 120:
                    idx += 1
                    continue
                break
            except StickersetInvalid:
                break

        upload = await client.invoke(
            raw.functions.messages.UploadMedia(
                peer=await client.resolve_peer(uid),
                media=raw.types.InputMediaUploadedDocument(
                    file=await client.save_file(file_path),
                    mime_type="image/webp",
                    attributes=[
                        raw.types.DocumentAttributeFilename(file_name="sticker.webp"),
                        raw.types.DocumentAttributeSticker(
                            alt="🙂",
                            stickerset=raw.types.InputStickerSetEmpty(),
                            mask=False
                        )
                    ]
                )
            )
        )

        doc = upload.document

        try:
            await client.invoke(
                raw.functions.stickers.AddStickerToSet(
                    stickerset=raw.types.InputStickerSetShortName(short_name=short),
                    sticker=raw.types.InputStickerSetItem(
                        document=raw.types.InputDocument(
                            id=doc.id,
                            access_hash=doc.access_hash,
                            file_reference=doc.file_reference
                        ),
                        emoji="🙂"
                    )
                )
            )
            created = False

        except StickersetInvalid:
            await client.invoke(
                raw.functions.stickers.CreateStickerSet(
                    user_id=await client.resolve_peer(uid),
                    title=f"{uname}'s Pack",
                    short_name=short,
                    stickers=[
                        raw.types.InputStickerSetItem(
                            document=raw.types.InputDocument(
                                id=doc.id,
                                access_hash=doc.access_hash,
                                file_reference=doc.file_reference
                            ),
                            emoji="🙂"
                        )
                    ]
                )
            )
            created = True

        await notify.edit(
            f"{'created' if created else 'added'}\nhttps://t.me/addstickers/{short}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("open pack", url=f"https://t.me/addstickers/{short}")]]
            )
        )

    except FloodWait as e:
        await notify.edit(f"wait {e.x}s")
    except RPCError as e:
        await notify.edit(f"error {e}")
    except Exception:
        await notify.edit(traceback.format_exc())
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
