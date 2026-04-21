from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import FloodWait
import asyncio

from Oneforall import app

PHOTO_URL = "https://graph.org/file/9bd106140750787f62681-320f969c2b6662e42a.jpg"


@app.on_message(filters.command("inviteall"))
async def invite_all(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # ✅ Admin Check
    member = await app.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await message.reply_text(
            "<blockquote>❌ Only admins can use this.</blockquote>",
            parse_mode=ParseMode.HTML
        )

    # 🔍 Check VC
    chat = await app.get_chat(chat_id)
    if not chat.voice_chat_started:
        return await message.reply_text(
            "<blockquote>❌ No active VC found.</blockquote>",
            parse_mode=ParseMode.HTML
        )

    # 🔗 Invite link
    invite_link = await app.export_chat_invite_link(chat_id)

    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🎤 Join VC", url=invite_link)]]
    )

    # 🚀 Start message
    status = await message.reply_photo(
        photo=PHOTO_URL,
        caption="<blockquote>🚀 Inviting members to VC...\n⏳ Please wait...</blockquote>",
        parse_mode=ParseMode.HTML
    )

    users = []
    count = 0

    # 🔄 Collect users
    async for member in app.get_chat_members(chat_id):
        if member.user.is_bot:
            continue
        if member.user.is_deleted:
            continue

        # mention format
        if member.user.username:
            users.append(f"@{member.user.username}")
        else:
            users.append(f"<a href='tg://user?id={member.user.id}'>user</a>")

    # 📢 Send in batches (avoid flood)
    batch_size = 5   # ⚡ safe limit (increase = risk)
    delay = 5        # seconds

    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]

        try:
            await message.reply_text(
                "<blockquote>🎤 Join VC now!\n\n" + " ".join(batch) + "</blockquote>",
                parse_mode=ParseMode.HTML,
                reply_markup=buttons,
                disable_web_page_preview=True
            )
            count += len(batch)
            await asyncio.sleep(delay)

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except Exception:
            continue

    # ✅ Done
    await status.edit_caption(
        f"<blockquote>✅ VC Invite Sent!\n\n👥 Users Notified: {count}</blockquote>",
        parse_mode=ParseMode.HTML
        )
