import random

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

import config
from config import BANNED_USERS, lyrical
from Oneforall import YouTube, app
from Oneforall.utils.database import (
    is_autoplay_on,
    get_autoplay_mood,
    set_autoplay,
    set_autoplay_mood,
)
from Oneforall.utils.decorators.language import languageCB
from Oneforall.utils.inline import (
    autoplay_mood_markup,
    autoplay_language_markup,
)

# Store previous tracks per chat
previous_tracks = {}


def askip_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "sᴋɪᴘ",
                    callback_data="askip",
                ),
                InlineKeyboardButton(
                    "ᴄʟᴏsᴇ",
                    callback_data="close",
                ),
            ]
        ]
    )


@app.on_message(filters.command("songconfig") & filters.group & ~BANNED_USERS)
@languageCB
async def songconfig_command(client, message, _):

    await message.reply_text(
        "🎵 **ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ**\n\n"
        "sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴏᴏᴅ:",
        reply_markup=autoplay_mood_markup(),
    )


@app.on_callback_query(filters.regex(r"^songconfig_mood:"))
@languageCB
async def handle_mood_selection(client, CallbackQuery, _):

    chat_id = CallbackQuery.message.chat.id

    try:
        mood = CallbackQuery.data.split(":", 1)[1]
    except Exception:
        return await CallbackQuery.answer(
            "ɪɴᴠᴀʟɪᴅ ᴍᴏᴏᴅ sᴇʟᴇᴄᴛɪᴏɴ",
            show_alert=True,
        )

    if chat_id not in lyrical:
        lyrical[chat_id] = {}

    lyrical[chat_id]["autoplay_mood"] = mood

    # Remove old buttons
    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass

    await CallbackQuery.answer(
        f"🎵 ᴍᴏᴏᴅ: {mood.title()}",
        show_alert=False,
    )

    await CallbackQuery.message.reply_text(
        "🌐 **sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ʟᴀɴɢᴜᴀɢᴇ:**",
        reply_markup=autoplay_language_markup(),
    )


@app.on_callback_query(filters.regex(r"^songconfig_language:"))
@languageCB
async def handle_language_selection(client, CallbackQuery, _):

    chat_id = CallbackQuery.message.chat.id

    try:
        language = CallbackQuery.data.split(":", 1)[1]
    except Exception:
        return await CallbackQuery.answer(
            "ɪɴᴠᴀʟɪᴅ ʟᴀɴɢᴜᴀɢᴇ sᴇʟᴇᴄᴛɪᴏɴ",
            show_alert=True,
        )

    if chat_id not in lyrical:
        lyrical[chat_id] = {}

    mood = lyrical[chat_id].get("autoplay_mood", "chill")

    await set_autoplay(chat_id, True)

    await set_autoplay_mood(
        chat_id,
        {
            "mood": mood,
            "language": language,
        },
    )

    lyrical[chat_id].pop("autoplay_mood", None)

    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass

    # Dialogue box
    await CallbackQuery.answer(
        f"✅ ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ\n🎵 {mood.title()}\n🌐 {language.title()}",
        show_alert=True,
    )

    await CallbackQuery.message.reply_text(
        "✅ **ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ**\n\n"
        f"🎵 ᴍᴏᴏᴅ: `{mood.title()}`\n"
        f"🌐 ʟᴀɴɢᴜᴀɢᴇ: `{language.title()}`"
    )


@app.on_callback_query(filters.regex(r"^AutoPlay"))
@languageCB
async def toggle_autoplay(client, CallbackQuery, _):

    callback_data = CallbackQuery.data.strip()

    try:
        chat_id = int(callback_data.split("|")[1])
    except Exception:
        return await CallbackQuery.answer(
            "ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ",
            show_alert=True,
        )

    autoplay_status = await is_autoplay_on(chat_id)

    # Disable autoplay
    if autoplay_status:

        await set_autoplay(chat_id, False)

        try:
            await CallbackQuery.message.edit_reply_markup(None)
        except:
            pass

        # Dialogue box only
        return await CallbackQuery.answer(
            "❌ ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ",
            show_alert=True,
        )

    # Enable setup
    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass

    await CallbackQuery.answer()

    await CallbackQuery.message.reply_text(
        "🎵 **ᴇɴᴀʙʟᴇ ᴀᴜᴛᴏᴘʟᴀʏ**\n\n"
        "sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴏᴏᴅ:",
        reply_markup=autoplay_mood_markup(),
    )


@app.on_message(filters.command("askip") & filters.group & ~BANNED_USERS)
@languageCB
async def autoplay_skip_command(client, message, _):

    chat_id = message.chat.id

    await process_autoplay_skip(
        chat_id,
        message,
    )


@app.on_callback_query(filters.regex("^askip$"))
@languageCB
async def autoplay_skip_callback(client, CallbackQuery, _):

    chat_id = CallbackQuery.message.chat.id

    await CallbackQuery.answer("⏭ sᴋɪᴘᴘɪɴɢ...")

    await process_autoplay_skip(
        chat_id,
        CallbackQuery.message,
    )


async def process_autoplay_skip(chat_id, message):

    from Oneforall.core.call import Hotty

    autoplay_status = await is_autoplay_on(chat_id)

    if not autoplay_status:
        return await message.reply_text(
            "❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**"
        )

    try:
        track_data, track_id = await get_autoplay_recommendation(chat_id)

        if not track_data or not track_id:
            return await message.reply_text(
                "❌ **ɴᴏ ɴᴇxᴛ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ ғᴏᴜɴᴅ**"
            )

        title = track_data.get("title", "Unknown")
        duration_min = track_data.get("duration", "Unknown")
        thumbnail = track_data.get("thumb")

        try:
            file_path, direct = await YouTube.download(
                track_id,
                None,
                videoid=True,
                video=False,
            )
        except Exception as e:
            print(f"Download Error: {e}")

            return await message.reply_text(
                "❌ **ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ sᴏɴɢ**"
            )

        try:

            await Hotty.skip_stream(
                chat_id,
                file_path,
                video=None,
            )

        except Exception as e:
            print(f"Change Stream Error: {e}")

            return await message.reply_text(
                "❌ **ғᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴀɴɢᴇ sᴛʀᴇᴀᴍ**"
            )

        try:

            await app.send_photo(
                chat_id=chat_id,
                photo=thumbnail if thumbnail else config.YOUTUBE_IMG_URL,
                caption=(
                    "<blockquote>⚙️ **𝐒ʈʀ𝛆ɑɱ𝛆ɗ 𝐀ᴜᴛ๏ᴘɭɑɣ 𝐒ᴋɩᴘᴘ𝛆ɗ ✮**</blockquote>\n\n"
                    f"<blockquote>🦋 **𝐍๏Ꮗ 𝐀ᴜᴛ๏ᴘɭɑɣɩŋʛ :** {title[:40]}\n"
                    f"🕐 **𝐃ʋɽɑʈɩσŋ :** {duration_min}</blockquote>\n"
                    f"<blockquote><b>𝐏ɭᴜɢɩŋ 𝐃𝛆ᴠ𝛆ɭ๏ᴘ𝛆ɗ 𝐅ɩη𝛆ɭɣ 𝐁ɣ </b><a href='https://t.me/theinfinitynetwork'>˹𝐒η๏ᴡɣ 𝐍𝛆ʈᴡ๏ʀᴋ˼</a></blockquote>\n"
                ),
                reply_markup=askip_markup(),
            )

        except Exception as e:
            print(f"Thumbnail Send Error: {e}")

    except Exception as e:
        print(f"Askip Error: {e}")

        return await message.reply_text(
            "❌ **ғᴀɪʟᴇᴅ ᴛᴏ sᴋɪᴘ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ**"
        )


async def get_autoplay_recommendation(chat_id: int):

    if chat_id not in previous_tracks:
        previous_tracks[chat_id] = []

    mood_data = await get_autoplay_mood(chat_id)

    mood = "chill"
    language = "english"

    if isinstance(mood_data, dict):
        mood = mood_data.get("mood", "chill")
        language = mood_data.get("language", "english")

    used_ids = [x["vidid"] for x in previous_tracks[chat_id]]

    for _ in range(10):

        query = (
            f"{random.choice(['best', 'top', 'viral', 'popular'])} "
            f"{language} {mood} songs"
        )

        try:
            track_data, track_id = await YouTube.track(query)

            if not track_data or not track_id:
                continue

            if track_id in used_ids:
                continue

            if len(previous_tracks[chat_id]) >= 10:
                previous_tracks[chat_id].pop(0)

            previous_tracks[chat_id].append(
                {
                    "title": track_data.get("title"),
                    "vidid": track_id,
                    "mood": mood,
                    "language": language,
                }
            )

            return track_data, track_id

        except Exception as e:
            print(f"Autoplay Error: {e}")
            continue

    return None, None
