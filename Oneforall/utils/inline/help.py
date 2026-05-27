from typing import Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ButtonStyle
from Oneforall import app

# Combined help buttons integrating from both help.py and buttons.py
HELP_BUTTONS = [
    (_["H_B_1"], "help_callback hb1"),
    (_["H_B_2"], "help_callback hb2"),
    (_["H_B_3"], "help_callback hb3"),
    (_["H_B_4"], "help_callback hb4"),
    (_["H_B_5"], "help_callback hb5"),
    (_["H_B_6"], "help_callback hb6"),
    (_["H_B_7"], "help_callback hb7"),
    (_["H_B_8"], "help_callback hb8"),
    (_["H_B_9"], "help_callback hb9"),
    (_["H_B_10"], "help_callback hb10"),
    (_["H_B_11"], "help_callback hb11"),
    (_["H_B_12"], "help_callback hb12"),
    (_["H_B_13"], "help_callback hb13"),
    (_["H_B_14"], "help_callback hb14"),
    (_["H_B_15"], "help_callback hb15"),
    (_["H_B_26"], "help_callback hb17"),
    (_["H_B_25"], "help_callback hb16"),
    ("🎮 ғᴜɴ ɢᴀᴍᴇ", "help_callback hb21"),
    (_["H_B_27"], "help_callback hb18"),
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
                    callback_data=f"settings_back_helper",
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
                # Use label as-is (can be translated via language files if needed)
                button_text = _[label] if label in _ else label
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
            text="ᴅᴇʟᴇᴛᴇ",
            callback_data="close_help_group",
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
