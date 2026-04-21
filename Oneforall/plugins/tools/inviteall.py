from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserPrivacyRestricted, UserAlreadyParticipant
import asyncio

from Oneforall import app
from Oneforall.core.userbot import userbot

# 🔥 Yaha apna image URL ya file_id daal
PHOTO_URL = "https://graph.org/file/9bd106140750787f62681-320f969c2b6662e42a.jpg"


@app.on_message(filters.command("inviteall"))
async def invite_all(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # ✅ Admin Check
    member = await app.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await message.reply_text(
            "<blockquote>❌ Only admins can use this command.</blockquote>",
            parse_mode="html"
        )

    # 🚀 Start Message with Image
    msg = await message.reply_photo(
        photo=PHOTO_URL,
        caption="<blockquote>🚀 Inviting all members to VC...\n⏳ Please wait...</blockquote>",
        parse_mode="html"
    )

    success = 0
    failed = 0

    async for member in userbot.get_chat_members(chat_id):
        try:
            if member.user.is_bot:
                continue

            await userbot.add_chat_members(chat_id, member.user.id)

            success += 1
            await asyncio.sleep(2)  # ⚡ Safe delay

        except UserAlreadyParticipant:
            continue

        except UserPrivacyRestricted:
            failed += 1

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except Exception:
            failed += 1

    # ✅ Final Result (Edit same message)
    await msg.edit_caption(
        f"<blockquote>✅ Invite Completed!\n\n✔️ Success: {success}\n❌ Failed: {failed}</blockquote>",
        parse_mode="html"
    )
