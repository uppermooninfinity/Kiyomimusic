import math
import time
from pyrogram.enums import ButtonStyle

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Oneforall import app
from Oneforall.utils.formatters import time_to_seconds

from Oneforall.utils.stream.thumbnail import get_thumbnail_status


def get_button_style():
    """Get button style that cycles every 5 seconds: PRIMARY -> SUCCESS -> DANGER"""
    cycle = int(time.time()) % 15
    if cycle < 5:
        return ButtonStyle.PRIMARY
    elif cycle < 10:
        return ButtonStyle.SUCCESS
    else:
        return ButtonStyle.DANGER


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎚️ ꜰɪʟᴛᴇʀs",
                callback_data=f"ShowFilters {videoid}|{user_id}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons


def stream_markup_timer(_, vidid, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    umm = math.floor(percentage)

    if 0 < umm <= 10:
        bar = "|♬—————————|"
    elif 10 < umm < 20:
        bar = "|—♬————————|"
    elif 20 <= umm < 30:
        bar = "|——♬———————|"
    elif 30 <= umm < 40:
        bar = "|———♬——————|"
    elif 40 <= umm < 50:
        bar = "|————♬—————|"
    elif 50 <= umm < 60:
        bar = "|—————♬————|"
    elif 60 <= umm < 70:
        bar = "|——————♬———|"
    elif 70 <= umm < 80:
        bar = "|———————♬——|"
    elif 80 <= umm < 95:
        bar = "|————————♬—|"
    else:
        bar = "|—————————♬|"

    thumb_status = get_thumbnail_status(chat_id)

    thumb_text = (
        "🖼 ᴛʜᴜᴍʙ: ✅"
        if thumb_status == "on"
        else "🖼 ᴛʜᴜᴍʙ: ❌"
    )

    button_style = get_button_style()

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
                style=button_style,
            )
        ],
        [
            InlineKeyboardButton(
                text="»",
                callback_data=f"ADMIN Skip|{chat_id}",
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text="▸",
                callback_data=f"ADMIN Pause|{chat_id}",
                style=ButtonStyle.PRIMARY
            ),
            InlineKeyboardButton(
                text="⟳",
                callback_data=f"ADMIN Replay|{chat_id}",
                style=ButtonStyle.DANGER
            ),
        ],
        [
            InlineKeyboardButton(text="♫", callback_data=f"AutoPlay|{chat_id}"),
            InlineKeyboardButton(text=thumb_text, callback_data=f"THUMBTOGGLE|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style=ButtonStyle.SUCCESS
            )
        ],
        [
            InlineKeyboardButton(text="༎ຶ ᴀᴅᴅ ᴍᴇ ༎ຶ", url="https://t.me/Snowy_x_musicbot?startgroup=true"),
        ],
    ]

    return buttons


def stream_markup(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="༎ຶ ᴀᴅᴅ ᴍᴇ ༎ຶ", url="https://t.me/Snowy_x_musicbot?startgroup=true"),
        ],
    ]
    return buttons


def autoplay_mood_markup():
    moods = [
        ("ʜᴀᴘᴘʏ", "happy"),
        ("sᴀᴅ", "sad"),
        ("ᴇɴᴇʀɢᴇᴛɪᴄ", "energetic"),
        ("ᴄʜɪʟʟ", "chill"),
        ("ʀᴏᴄᴋ", "rock"),
        ("ᴘᴏᴘ", "pop"),
        ("ʜɪᴘ-ʜᴏᴘ", "hip-hop"),
        ("ᴊᴀᴢᴢ", "jazz"),
    ]

    buttons = []

    for i in range(0, len(moods), 2):
        row = [
            InlineKeyboardButton(
                text=moods[i][0],
                callback_data=f"songconfig_mood:{moods[i][1]}"
            )
        ]

        if i + 1 < len(moods):
            row.append(
                InlineKeyboardButton(
                    text=moods[i + 1][0],
                    callback_data=f"songconfig_mood:{moods[i + 1][1]}"
                )
            )

        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ ᴄʟᴏsᴇ",
                callback_data="close"
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


def autoplay_language_markup():
    """Generate language selection buttons for autoplay"""

    languages = [
        ("ᴇɴɢʟɪsʜ", "english"),
        ("ʜɪɴᴅɪ", "hindi"),
        ("sᴘᴀɴɪsʜ", "spanish"),
        ("ғʀᴇɴᴄʜ", "french"),
        ("ɢᴇʀᴍᴀɴ", "german"),
        ("ᴊᴀᴘᴀɴᴇsᴇ", "japanese"),
        ("ᴋᴏʀᴇᴀɴ", "korean"),
        ("ᴘᴏʀᴛᴜɢᴜᴇsᴇ", "portuguese"),
    ]

    buttons = []

    for i in range(0, len(languages), 2):
        row = [
            InlineKeyboardButton(
                text=languages[i][0],
                callback_data=f"songconfig_language:{languages[i][1]}"
            )
        ]

        if i + 1 < len(languages):
            row.append(
                InlineKeyboardButton(
                    text=languages[i + 1][0],
                    callback_data=f"songconfig_language:{languages[i + 1][1]}"
                )
            )

        buttons.append(row)

    buttons.append(
        [InlineKeyboardButton(text="❌ ᴄʟᴏsᴇ", callback_data="close")]
    )

    return InlineKeyboardMarkup(buttons)


def filters_markup_page_1():
    """Display first page of filters"""
    filters = [
        ("🔊 ʙᴀss ʙᴏᴏst", "bass_boost"),
        ("📈 ᴛʀᴇʙʟᴇ ʙᴏᴏst", "treble_boost"),
        ("🎵 ᴇᴄʜᴏ", "echo"),
        ("🔄 ʀᴇᴠᴇʀʙ", "reverb"),
        ("🎶 ᴄʜᴏʀᴜs", "chorus"),
        ("📊 ᴄᴏᴍᴘʀᴇssᴏʀ", "compressor"),
    ]

    buttons = []
    for filter_name, filter_key in filters:
        buttons.append([
            InlineKeyboardButton(
                text=filter_name,
                callback_data=f"ApplyFilter {filter_key}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="▷ ɴᴇxᴛ ᴘᴀɢᴇ",
            callback_data="FiltersPage 2"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="❌ ᴄʟᴏsᴇ",
            callback_data="close"
        )
    ])

    return InlineKeyboardMarkup(buttons)


def filters_markup_page_2():
    """Display second page of filters"""
    filters = [
        ("🎸 ʀᴏᴄᴋ ᴇq", "equalizer_rock"),
        ("🎤 ᴘᴏᴘ ᴇq", "equalizer_pop"),
        ("🎺 ᴊᴀᴢᴢ ᴇq", "equalizer_jazz"),
        ("⚖️ ɴᴏʀᴍᴀʟɪᴢᴇʀ", "normalizer"),
        ("🔀 sᴛᴇʀᴇᴏ ᴡɪᴅᴇɴᴇʀ", "stereo_widener"),
        ("⬆️ ᴘɪᴛᴄʜ ᴜᴘ", "pitch_up"),
    ]

    buttons = []
    for filter_name, filter_key in filters:
        buttons.append([
            InlineKeyboardButton(
                text=filter_name,
                callback_data=f"ApplyFilter {filter_key}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="◁ ᴘʀᴇᴠ ᴘᴀɢᴇ",
            callback_data="FiltersPage 1"
        ),
        InlineKeyboardButton(
            text="▷ ɴᴇxᴛ ᴘᴀɢᴇ",
            callback_data="FiltersPage 3"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="❌ ᴄʟᴏsᴇ",
            callback_data="close"
        )
    ])

    return InlineKeyboardMarkup(buttons)


def filters_markup_page_3():
    """Display third page of filters"""
    filters = [
        ("⬇️ ᴘɪᴛᴄʜ ᴅᴏᴡɴ", "pitch_down"),
        ("🔆 ꜰᴀᴅᴇ ɪɴ", "fade_in"),
        ("🔅 ꜰᴀᴅᴇ ᴏᴜᴛ", "fade_out"),
        ("🔇 ɴᴏɪsᴇ ʀᴇᴅ.", "noise_reduction"),
        ("💿 ᴠɪɴʏʟ", "vinyl"),
        ("☎️ ᴛᴇʟᴇᴘʜᴏɴᴇ", "telephone"),
    ]

    buttons = []
    for filter_name, filter_key in filters:
        buttons.append([
            InlineKeyboardButton(
                text=filter_name,
                callback_data=f"ApplyFilter {filter_key}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="◁ ᴘʀᴇᴠ ᴘᴀɢᴇ",
            callback_data="FiltersPage 2"
        ),
        InlineKeyboardButton(
            text="▷ ɴᴇxᴛ ᴘᴀɢᴇ",
            callback_data="FiltersPage 4"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="❌ ᴄʟᴏsᴇ",
            callback_data="close"
        )
    ])

    return InlineKeyboardMarkup(buttons)


def filters_markup_page_4():
    """Display fourth page of filters"""
    filters = [
        ("📡 ʜɪɢʜ ᴘᴀss", "high_pass"),
        ("🔊 ʟᴏᴡ ᴘᴀss", "low_pass"),
    ]

    buttons = []
    for filter_name, filter_key in filters:
        buttons.append([
            InlineKeyboardButton(
                text=filter_name,
                callback_data=f"ApplyFilter {filter_key}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="❌ ɴᴏ ꜰɪʟᴛᴇʀ",
            callback_data="ApplyFilter no_filter"
        ),
    ])

    buttons.append([
        InlineKeyboardButton(
            text="◁ ᴘʀᴇᴠ ᴘᴀɢᴇ",
            callback_data="FiltersPage 3"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="❌ ᴄʟᴏsᴇ",
            callback_data="close"
        )
    ])

    return InlineKeyboardMarkup(buttons)


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"brandedPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"brandedPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎚️ ꜰɪʟᴛᴇʀs",
                callback_data=f"ShowFilters {videoid}|{user_id}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons


## Telegram Markup


def telegram_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="ɴᴇxᴛ",
                callback_data=f"PanelMarkup None|{chat_id}",
            ),
            InlineKeyboardButton(text=_["CLOSEMENU_BUTTON"], callback_data="close"),
        ],
    ]
    return buttons


## Queue Markup


def queue_markup(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(
                text="II ᴘᴀᴜsᴇ",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
            InlineKeyboardButton(text="▢ sᴛᴏᴘ", callback_data=f"ADMIN Stop|{chat_id}"),
            InlineKeyboardButton(
                text="sᴋɪᴘ ‣‣I", callback_data=f"ADMIN Skip|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="▷ ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}"
            ),
            InlineKeyboardButton(
                text="ʀᴇᴘʟᴀʏ ↺", callback_data=f"ADMIN Replay|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎚️ ꜰɪʟᴛᴇʀs",
                callback_data=f"ShowFilters None|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⛦ ᴍᴏʀᴇ ❥",
                callback_data=f"PanelMarkup None|{chat_id}",
            ),
        ],
    ]

    return buttons


def stream_markup2(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="🎚️ ꜰɪʟᴛᴇʀs",
                callback_data=f"ShowFilters None|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(text=_["CLOSEMENU_BUTTON"], callback_data="close"),
        ],
    ]
    return buttons


def stream_markup_timer2(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    umm = math.floor(percentage)
    if 0 < umm <= 40:
        bar = "◉——————————"
    elif 10 < umm < 20:
        bar = "—◉—————————"
    elif 20 < umm < 30:
        bar = "——◉————————"
    elif 30 <= umm < 40:
        bar = "———◉———————"
    elif 40 <= umm < 50:
        bar = "————◉——————"
    elif 50 <= umm < 60:
        bar = "——————◉————"
    elif 50 <= umm < 70:
        bar = "———————◉———"
    else:
        bar = "——————————◉"

    button_style = get_button_style()

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
                style=button_style,
            )
        ],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="🎚️ ꜰɪʟᴛᴇʀs",
                callback_data=f"ShowFilters None|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(text=_["CLOSEMENU_BUTTON"], callback_data="close"),
        ],
    ]
    return buttons


def panel_markup_1(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎧 sᴜғғʟᴇ ❥",
                callback_data=f"ADMIN Shuffle|{chat_id}",
            ),
            InlineKeyboardButton(text="ʟᴏᴏᴘ ↺", callback_data=f"ADMIN Loop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="◁ 10 sᴇᴄ",
                callback_data=f"ADMIN 1|{chat_id}",
            ),
            InlineKeyboardButton(
                text="10 sᴇᴄ ▷",
                callback_data=f"ADMIN 2|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎚️ ꜰɪʟᴛᴇʀs",
                callback_data=f"ShowFilters None|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❥ ʜᴏᴍᴇ ❥",
                callback_data=f"Pages Back|2|{videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="❥ ɴᴇxᴛ ❥",
                callback_data=f"Pages Forw|2|{videoid}|{chat_id}",
            ),
        ],
    ]
    return buttons


def panel_markup_2(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🕒 0.5x",
                callback_data=f"SpeedUP {chat_id}|0.5",
            ),
            InlineKeyboardButton(
                text="🕓 0.75x",
                callback_data=f"SpeedUP {chat_id}|0.75",
            ),
            InlineKeyboardButton(
                text="🕤 1.0x",
                callback_data=f"SpeedUP {chat_id}|1.0",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🕤 1.5x",
                callback_data=f"SpeedUP {chat_id}|1.5",
            ),
            InlineKeyboardButton(
                text="🕛 2.0x",
                callback_data=f"SpeedUP {chat_id}|2.0",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❥ ʙᴀᴄᴋ ❥",
                callback_data=f"Pages Back|1|{videoid}|{chat_id}",
            ),
        ],
    ]
    return buttons


def panel_markup_5(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(text="ᴘᴀᴜsᴇ", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="sᴛᴏᴘ", callback_data=f"ADMIN Stop|{chat_id}"),
            InlineKeyboardButton(text="sᴋɪᴘ", callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}"
            ),
            InlineKeyboardButton(
                text="ʀᴇᴘʟᴀʏ", callback_data=f"ADMIN Replay|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="❥ ʜᴏᴍᴇ ❥",
                callback_data=f"MainMarkup {videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="❥ ɴᴇxᴛ ❥",
                callback_data=f"Pages Forw|1|{videoid}|{chat_id}",
            ),
        ],
    ]
    return buttons


def panel_markup_3(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="🕒 0.5x",
                callback_data=f"SpeedUP {chat_id}|0.5",
            ),
            InlineKeyboardButton(
                text="🕓 0.75x",
                callback_data=f"SpeedUP {chat_id}|0.75",
            ),
            InlineKeyboardButton(
                text="🕤 1.0x",
                callback_data=f"SpeedUP {chat_id}|1.0",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🕤 1.5x",
                callback_data=f"SpeedUP {chat_id}|1.5",
            ),
            InlineKeyboardButton(
                text="🕛 2.0x",
                callback_data=f"SpeedUP {chat_id}|2.0",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❥ ʙᴀᴄᴋ ❥",
                callback_data=f"Pages Back|2|{videoid}|{chat_id}",
            ),
        ],
    ]
    return buttons


def panel_markup_4(_, vidid, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    umm = math.floor(percentage)
    if 0 < umm <= 40:
        bar = "◉——————————"
    elif 10 < umm < 20:
        bar = "—◉—————————"
    elif 20 < umm < 30:
        bar = "——◉————————"
    elif 30 <= umm < 40:
        bar = "———◉———————"
    elif 40 <= umm < 50:
        bar = "————◉——————"
    elif 50 <= umm < 60:
        bar = "——————◉————"
    elif 50 <= umm < 70:
        bar = "———————◉———"
    else:
        bar = "——————————◉"

    button_style = get_button_style()

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
                style=button_style,
            )
        ],
        [
            InlineKeyboardButton(
                text="II ᴘᴀᴜsᴇ",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
            InlineKeyboardButton(
                text="▢ sᴛᴏᴘ ▢", callback_data=f"ADMIN Stop|{chat_id}"
            ),
            InlineKeyboardButton(
                text="sᴋɪᴘ ‣‣I", callback_data=f"ADMIN Skip|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="▷ ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}"
            ),
            InlineKeyboardButton(
                text="ʀᴇᴘʟᴀʏ ↺", callback_data=f"ADMIN Replay|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="❥ ʜᴏᴍᴇ ❥",
                callback_data=f"MainMarkup {vidid}|{chat_id}",
            ),
        ],
    ]

    return buttons


def panel_markup_clone(_, vidid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="📥 ᴠɪᴅᴇᴏ", callback_data=f"downloadvideo {vidid}"
            ),
            InlineKeyboardButton(
                text="📥 ᴀᴜᴅɪᴏ", callback_data=f"downloadaudio {vidid}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="✚ ᴘʟᴀʏʟɪsᴛ ✚", callback_data=f"branded_playlist {vidid}"
            ),
        ],
    ]

    return buttons
