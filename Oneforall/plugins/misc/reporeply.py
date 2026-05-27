from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from Oneforall import app
from config import REPO_VID_URL
from strings import get_string


# repo command
@app.on_message(filters.command("repo") & filters.private)
async def repo_reply(_, message: Message):
    strings = get_string("en")

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⦿ ʙᴀᴄᴋ ⦿",
                    callback_data="help_back"
                )
            ]
        ]
    )

    await message.reply_video(
        video=REPO_VID_URL,
        caption=strings["repocaption"],
        has_spoiler=True,
        reply_markup=buttons,
    )


# callback query for repo button
@app.on_callback_query(filters.regex("^repo$"))
async def repo_callback(_, query: CallbackQuery):
    strings = get_string("en")

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⦿ ʙᴀᴄᴋ ⦿",
                    callback_data="help_back"
                )
            ]
        ]
    )

    await query.message.edit_media(
        media={
            "type": "video",
            "media": REPO_VID_URL,
            "caption": strings["repocaption"],
        },
        reply_markup=buttons,
    )

@app.on_callback_query(filters.regex("^help_back$"))
async def help_back(_, query: CallbackQuery):
    await query.message.edit_text(
        text="<",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "☁️sᴏᴜʀᴄᴇ☁️",
                        callback_data="repo"
                    )
                ]
            ]
        ),
    )
