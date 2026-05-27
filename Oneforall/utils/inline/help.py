from typing import Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ButtonStyle
from Oneforall import app

# Combined help buttons integrating from both help.py and buttons.py
HELP_BUTTONS = [
    (["H_B_1"], "mplus help_callback hb1"),
    (["H_B_2"], "mplus help_callback hb2"),
    (["H_B_3"], "mplus help_callback hb3"),
    (["H_B_4"], "mplus help_callback hb4"),
    (["H_B_5"], "mplus help_callback hb5"),
    (["H_B_6"], "mplus help_callback hb6"),
    (["H_B_7"], "mplus help_callback hb7"),
    (["H_B_8"], "mplus help_callback hb8"),
    (["H_B_9"], "mplus help_callback hb9"),
    (["H_B_10"], "mplus help_callback hb10"),
    (["H_B_11"], "mplus help_callback hb11"),
    (["H_B_12"], "mplus help_callback hb12"),
    (["H_B_13"], "mplus help_callback hb13"),
    (["H_B_14"], "mplus help_callback hb14"),
    (["H_B_15"], "mplus help_callback hb15"),
    (["H_B_26"], "mplus help_callback hb17"),
    (["H_B_25"], "mplus help_callback hb16"),
    ("🎮 ғᴜɴ ɢᴀᴍᴇ", "help_callback hb21"),
    (["H_B_27"], "mplus help_callback hb18"),
    ("Hɪsᴛᴏʀʏ", "HELP_History"),
    ("Tᴀɢ-Aʟʟ", "HELP_TagAll"),
    ("Iɴꜰᴏ", "HELP_Info"),
    ("Exᴛʀᴀ", "HELP_Extra"),
    ("ᴄᴏᴜᴘʟᴇꜱ", "HELP_Couples"),
    ("Aᴄᴛɪᴏɴ", "HELP_Action"),
    ("Sᴇᴀʀᴄʜ", "HELP_Search"),
    ("ғᴏɴᴛ", "HELP_Font"),
    ("Bᴏᴛs", "HELP_Bots"),
    ("Ⓣ-ɢʀᴀᴘʜ", "HELP_TG"),
    ("Sᴏᴜʀᴄᴇ", "HELP_Source"),
    ("Tʀᴜᴛʜ-ᗪᴀʀᴇ", "HELP_TD"),
    ("Qᴜɪᴢ", "HELP_Quiz"),
    ("ᴛᴛs", "HELP_TTS"),
    ("Rᴀᴅɪᴏ", "HELP_Radio"),
    ("ǫᴜᴏᴛʟʏ", "HELP_Q"),
    ("ᴛʜᴜᴍʙ", "HELP_Thumb"),
    ("ᴀᴜᴛᴏᴘʟᴀʏ", "HELP_Autoplay"),
    ("✨ ғsᴜʙ", "HELP_Sub"),
    ("🎮 ғᴜɴ ɢᴀᴍᴇ", "HELP_Fun"),
]


def help_pannel(_, START: Union[bool, int] = None):
    """Create main help panel with 3x3 pagination"""
    # Use the new pagination function with page 0
    return group_help_pagination(_, page=0)


def help_back_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"settingsback_helper",
                ),
            ]
        ]
    )
    return upl


def private_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_4"],
                url=f"https://t.me/{app.username}?start=help",
            ),
        ],
    ]
    return buttons


def group_help_pagination(_, page: int = 0):
    """Create paginated help buttons in 3x3 grid format
    
    Displays 9 buttons per page (3x3 grid) with pagination controls.
    Integrates all buttons from both help.py and buttons.py.
    """
    buttons_per_page = 9  # 3x3 grid
    total_buttons = len(HELP_BUTTONS)
    total_pages = (total_buttons + buttons_per_page - 1) // buttons_per_page
    
    # Ensure page is within bounds
    page = max(0, min(page, total_pages - 1))
    
    # Get buttons for current page
    start_idx = page * buttons_per_page
    end_idx = min(start_idx + buttons_per_page, total_buttons)
    page_buttons = HELP_BUTTONS[start_idx:end_idx]
    
    # Build 3x3 grid
    keyboard = []
    for i in range(0, len(page_buttons), 3):
        row = []
        for j in range(3):
            if i + j < len(page_buttons):
                label, callback = page_buttons[i + j]
                # Normalize label: extract from list if needed
                label_key = label[0] if isinstance(label, list) else label
                # Use label as-is (can be translated via language files if needed)
                button_text = _[label_key] if label_key in _ else label_key
                row.append(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"mplus {callback}",
                    )
                )
        if row:  # Only add non-empty rows
            keyboard.append(row)
    
    # Add pagination and navigation buttons
    nav_row = []
    
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="<",
                callback_data=f"group_help_page {page - 1}",
                style=ButtonStyle.SUCCESS,
            )
        )
    
    nav_row.append(
        InlineKeyboardButton(
            text="ʙᴀᴄᴋ",
            callback_data="settingsback_helper",
        )
    )
    
    if page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton(
                text=">",
                callback_data=f"group_help_page {page + 1}",
                style=ButtonStyle.SUCCESS,
            )
        )
    
    if nav_row:
        keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(keyboard)
