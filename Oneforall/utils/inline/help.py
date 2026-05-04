from typing import Union
import random
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Oneforall import app


PATTERNS = [
    [3, 2, 1],
    [2, 3, 1],
    [1, 3, 2],
]


def chunk_buttons(btns, pattern):
    rows = []
    i = 0
    p = 0

    while i < len(btns):
        size = pattern[p % len(pattern)]
        rows.append(btns[i:i + size])
        i += size
        p += 1

    return rows


def help_pannel(_, START: Union[bool, int] = None):
    # 🔒 stable randomness per session
    random.seed(42)

    # 🔹 All buttons list
    raw_buttons = [
        ("H_B_1", "hb1"), ("H_B_2", "hb2"), ("H_B_3", "hb3"),
        ("H_B_4", "hb4"), ("H_B_5", "hb5"), ("H_B_6", "hb6"),
        ("H_B_7", "hb7"), ("H_B_8", "hb8"), ("H_B_9", "hb9"),
        ("H_B_10", "hb10"), ("H_B_11", "hb11"), ("H_B_12", "hb12"),
        ("H_B_13", "hb13"), ("H_B_14", "hb14"),
        ("🎮 Fun Game", "hb21"), ("📢 Fsub", "hb20"),
    ]

    # 🔀 shuffle
    random.shuffle(raw_buttons)

    # ⭐ pick highlight
    highlight = raw_buttons.pop(0)

    highlight_btn = [
        InlineKeyboardButton(
            text=f"✨ {_ [highlight[0]] if highlight[0].startswith('H_') else highlight[0]}",
            callback_data=f"help_callback {highlight[1]}",
        )
    ]

    # 🔹 convert remaining buttons
    buttons = [
        InlineKeyboardButton(
            text=_[name] if name.startswith("H_") else name,
            callback_data=f"help_callback {cb}",
        )
        for name, cb in raw_buttons
    ]

    # 🎲 random pattern
    pattern = random.choice(PATTERNS)

    rows = chunk_buttons(buttons, pattern)

    # 🔥 inject highlight at top
    layout = [highlight_btn] + rows

    # 🔻 Navigation
    nav = [
        InlineKeyboardButton("<", callback_data=f"mbot_cb"),
        InlineKeyboardButton("🏡", callback_data="settingsback_helper"),
        InlineKeyboardButton(">", callback_data=f"mbot_cb"),
    ]

    close_btn = [InlineKeyboardButton("❌ Close", callback_data="close")]

    layout.append(nav if START else close_btn)

    return InlineKeyboardMarkup(layout)


def help_back_markup(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🔙 " + _["BACK_BUTTON"],
                    callback_data="settings_back_helper",
                )
            ]
        ]
    )


def private_help_panel(_):
    return [
        [
            InlineKeyboardButton(
                text="✨ " + _["S_B_4"],
                url=f"https://t.me/{app.username}?start=help",
            )
        ]
    ]
