import random
from pyrogram.types import InlineKeyboardButton


class BUTTONS(object):

    RAW = [
        ("CʜᴀᴛGPT", "HELP_ChatGPT"),
        ("Hɪsᴛᴏʀʏ", "HELP_History"),
        ("Rᴇᴇʟ", "HELP_Reel"),
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
    ]

    @staticmethod
    def build():
        random.seed()  # fresh feel every time

        data = BUTTONS.RAW.copy()
        random.shuffle(data)

        # ⭐ Highlight button
        top = data.pop(0)
        highlight = [
            InlineKeyboardButton(
                f"✨ {top[0]}", callback_data=f"mplus {top[1]}"
            )
        ]

        # 🎲 Pattern generator
        patterns = [[3, 2, 1], [2, 3, 1], [1, 3, 2]]
        pattern = random.choice(patterns)

        rows = []
        i = 0
        p = 0

        while i < len(data):
            size = pattern[p % len(pattern)]
            chunk = data[i:i + size]

            row = [
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"mplus {cb}",
                )
                for name, cb in chunk
            ]

            rows.append(row)

            i += size
            p += 1

        # 🎮 Special row (fixed bottom highlight)
        special = [
            InlineKeyboardButton("🎮 Qᴜɪᴢ", callback_data="mplus HELP_Quiz"),
            InlineKeyboardButton("🔥 Tʀᴜᴛʜ", callback_data="mplus HELP_TD"),
        ]

        # 🔻 Navigation
        nav = [
            InlineKeyboardButton("◁", callback_data="settings_back_helper"),
            InlineKeyboardButton("▷", callback_data="settings_back_helper"),
        ]

        return [highlight] + rows + [special, nav]
