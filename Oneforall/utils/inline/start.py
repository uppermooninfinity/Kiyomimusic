from pyrogram.types import InlineKeyboardButton
from pyrogram.enums import ButtonStyle
import config
from Oneforall import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true", style=ButtonStyle.SUCCESS
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT, style=ButtonStyle.PRIMARY),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_back_helper", style=ButtonStyle.SUCCESS),
        ],
        [
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT, style=ButtonStyle.SUCCESS),
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL, style=ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true", style=ButtonStyle.PRIMARY
            )
        ],
    ]
    return buttons
