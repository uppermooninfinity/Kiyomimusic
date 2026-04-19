from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ChatMemberStatus,
)

from Oneforall import app
from Oneforall.utils.database import set_thumb_mode, get_thumb_mode

def panel_text(status: bool):
    return (
        "⚙️ **sᴇᴛᴛɪɴɢs › ᴛʜᴜᴍʙɴᴀɪʟ**\n\n"
        "➻ ᴄᴏɴᴛʀᴏʟ ᴡʜᴇᴛʜᴇʀ ʙᴏᴛ sᴇɴᴅs ᴛʜᴜᴍʙɴᴀɪʟs ᴡɪᴛʜ sᴏɴɢs.\n\n"
        f"★ sᴛᴀᴛᴜs : {'🟢 ᴇɴᴀʙʟᴇᴅ' if status else '🔴 ᴅɪsᴀʙʟᴇᴅ'}\n\n"
        "› sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ :"
    )


def panel_buttons(status: bool):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 ᴏɴ" if not status else "✅ ᴏɴ",
                    callback_data="thumb_on",
                ),
                InlineKeyboardButton(
                    "🔴 ᴏғғ" if status else "✅ ᴏғғ",
                    callback_data="thumb_off",
                ),
            ],
            [
                InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="settings_back")
            ],
        ]
    )

@app.on_message(filters.command("thumb"))
async def thumb_command(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    member = await message.chat.get_member(user_id)

    if member.status not in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):
        return await message.reply_text(
            "❌ **ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ᴜsᴇ ᴛʜɪs.**"
        )

    status = await get_thumb_mode(chat_id)

    await message.reply_text(
        panel_text(status),
        reply_markup=panel_buttons(status),
    )

@app.on_callback_query(filters.regex("^thumb_on$"))
async def thumb_on_cb(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    member = await query.message.chat.get_member(user_id)

    if member.status not in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴄʜᴀɴɢᴇ ᴛʜɪs.", show_alert=True)

    await set_thumb_mode(chat_id, True)

    await query.answer("ᴛʜᴜᴍʙɴᴀɪʟ ᴇɴᴀʙʟᴇᴅ 🟢")

    status = True
    await query.message.edit_text(
        panel_text(status),
        reply_markup=panel_buttons(status),
    )

@app.on_callback_query(filters.regex("^thumb_off$"))
async def thumb_off_cb(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    member = await query.message.chat.get_member(user_id)

    if member.status not in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):
        return await query.answer("ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴄʜᴀɴɢᴇ ᴛʜɪs.", show_alert=True)

    await set_thumb_mode(chat_id, False)

    await query.answer("ᴛʜᴜᴍʙɴᴀɪʟ ᴅɪsᴀʙʟᴇᴅ 🔴")

    status = False
    await query.message.edit_text(
        panel_text(status),
        reply_markup=panel_buttons(status),
  )
