import random
import asyncio
import time

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
from Oneforall.utils.spotify_image import (
    create_spotify_thumbnail_with_yt_image,
    save_image_to_bytes,
    format_time,
)

# Store previous tracks per chat
previous_tracks = {}
# Store current playing track info per chat
current_autoplay_track = {}
# Store autoplay queues per chat
autoplay_queue = {}
# Store message IDs for progress bar updates
progress_messages = {}
# Track update tasks
update_tasks = {}


def askip_markup(chat_id=None, current_sec=0, total_sec=0):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⏮ 0:00" if not chat_id else f"⏮ {format_time(current_sec)}/{format_time(total_sec)}",
                    callback_data=f"aprogress|{chat_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⏭ sᴋɪᴘ",
                    callback_data="askip",
                ),
                InlineKeyboardButton(
                    "📋 Qᴜᴇᴜᴇ",
                    callback_data=f"aqueue|{chat_id}",
                ),
                InlineKeyboardButton(
                    "ᴄʟᴏsᴇ",
                    callback_data="close",
                ),
            ]
        ]
    )


@app.on_message(filters.command("mconfig") & filters.group & ~BANNED_USERS)
@languageCB
async def songconfig_command(client, message, _):

    await message.reply_text(
        "<blockquote>🎵 **ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ**\n\n"
        "sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴏᴏᴅ:</blockquote>",
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
        "<blockquote>🌐 **sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ʟᴀɴɢᴜᴀɢᴇ:**</blockquote>",
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
        f"<blockquote>✅ ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ\n🎵 {mood.title()}\n🌐 {language.title()}</blockquote>",
        show_alert=True,
    )

    await CallbackQuery.message.reply_text(
        "<blockquote>✅ **ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ**\n\n"
        f"🎵 ᴍᴏᴏᴅ: `{mood.title()}`\n"
        f"🌐 ʟᴀɴɢᴜᴀɢᴇ: `{language.title()}`</blockquote>"
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
        "<blockquote>🎵 **ᴇɴᴀʙʟᴇ ᴀᴜᴛᴏᴘʟᴀʏ**\n\n"
        "sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴏᴏᴅ:</blockquote>",
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


@app.on_message(filters.command("aseek") & filters.group & ~BANNED_USERS)
@languageCB
async def autoplay_seek_command(client, message, _):
    """Seek to a specific time in the autoplay song"""
    
    chat_id = message.chat.id
    
    autoplay_status = await is_autoplay_on(chat_id)
    
    if not autoplay_status:
        return await message.reply_text(
            "<blockquote>❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**</blockquote>"
        )
    
    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) < 2:
            return await message.reply_text(
                "<blockquote>📍 **ᴜsᴀɢᴇ:** /aseek <minutes> <seconds>\n"
                "ᴇxᴀᴍᴘʟᴇ: /aseek 1 30</blockquote>"
            )
        
        try:
            minutes = int(cmd_parts[1])
            seconds = int(cmd_parts[2]) if len(cmd_parts) > 2 else 0
        except (ValueError, IndexError):
            return await message.reply_text(
                "<blockquote>❌ **ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ғᴏʀᴍᴀᴛ**\n"
                "ᴜsᴇ: /aseek <minutes> <seconds>\n"
                "ᴇxᴀᴍᴘʟᴇ: /aseek 1 30</blockquote>"
            )
        
        total_seconds = minutes * 60 + seconds
        
        from Oneforall.core.call import Hotty
        
        if chat_id in current_autoplay_track:
            await Hotty.seek_stream(chat_id, total_seconds)
            
            await message.reply_text(
                f"<blockquote>📍 **sᴇᴇᴋɪɴɢ ᴛᴏ:** {format_time(total_seconds)}</blockquote>"
            )
        else:
            await message.reply_text(
                "<blockquote>❌ **ɴᴏ sᴏɴɢ ᴄᴜʀʀᴇɴᴛʟʏ ᴘʟᴀʏɪɴɢ**</blockquote>"
            )
    
    except Exception as e:
        print(f"Seek Error: {e}")
        await message.reply_text(
            "<blockquote>❌ **ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴇᴋ sᴏɴɢ**</blockquote>"
        )


@app.on_message(filters.command("aqueue") & filters.group & ~BANNED_USERS)
@languageCB
async def autoplay_queue_command(client, message, _):
    """Show the autoplay queue"""
    
    chat_id = message.chat.id
    
    autoplay_status = await is_autoplay_on(chat_id)
    
    if not autoplay_status:
        return await message.reply_text(
            "<blockquote>❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**</blockquote>"
        )
    
    if chat_id not in previous_tracks or not previous_tracks[chat_id]:
        return await message.reply_text(
            "<blockquote>📭 **qᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ**</blockquote>"
        )
    
    queue_text = "<blockquote>📋 **ᴀᴜᴛᴏᴘʟᴀʏ qᴜᴇᴜᴇ**\n\n"
    
    if chat_id in current_autoplay_track:
        current = current_autoplay_track[chat_id]
        queue_text += f"▶️ **ɴᴏᴡ ᴘʟᴀʏɪɴɢ:**\n"
        queue_text += f"🎵 {current.get('title', 'Unknown')[:50]}\n"
        queue_text += f"🕐 {current.get('duration', 'Unknown')}\n\n"
    
    queue_text += f"**ᴜᴘᴄᴏᴍɪɴɢ ᴛʀᴀᴄᴋs ({len(previous_tracks[chat_id])}):**\n\n"
    
    for idx, track in enumerate(previous_tracks[chat_id][:10], 1):
        title = track.get("title", "Unknown")[:45]
        queue_text += f"{idx}. {title}\n"
    
    if len(previous_tracks[chat_id]) > 10:
        queue_text += f"\n... ᴀɴᴅ {len(previous_tracks[chat_id]) - 10} ᴍᴏʀᴇ\n"
    
    queue_text += "</blockquote>"
    
    await message.reply_text(queue_text)


@app.on_callback_query(filters.regex("^aqueue\\|"))
@languageCB
async def autoplay_queue_callback(client, CallbackQuery, _):
    """Show queue from button - FIXED to avoid message too long error"""
    
    chat_id = int(CallbackQuery.data.split("|")[1])
    
    autoplay_status = await is_autoplay_on(chat_id)
    
    if not autoplay_status:
        return await CallbackQuery.answer(
            "❌ ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ",
            show_alert=True,
        )
    
    if chat_id not in previous_tracks or not previous_tracks[chat_id]:
        return await CallbackQuery.answer(
            "📭 qᴜᴇᴜᴇ ᴇᴍᴘᴛʏ",
            show_alert=True,
        )
    
    # Build queue text with character limit (max 4096 for callback, but we use 3500 to be safe)
    queue_text = "📋 **ᴀᴜᴛᴏᴘʟᴀʏ Qᴜᴇᴜᴇ**\n"
    
    if chat_id in current_autoplay_track:
        current = current_autoplay_track[chat_id]
        queue_text += f"▶️ {current.get('title', 'Unknown')[:40]}\n"
    
    queue_text += "\n**ᴜᴘᴄᴏᴍɪɴɢ:**\n"
    
    char_count = len(queue_text)
    track_count = 0
    
    # Add tracks until we hit character limit
    for idx, track in enumerate(previous_tracks[chat_id], 1):
        title = track.get("title", "Unknown")[:40]
        line = f"{idx}. {title}\n"
        
        if char_count + len(line) > 3500:
            remaining = len(previous_tracks[chat_id]) - idx
            if remaining > 0:
                queue_text += f"\n... ᴀɴᴅ {remaining} ᴍᴏʀᴇ"
            break
        
        queue_text += line
        char_count += len(line)
        track_count += 1
    
    await CallbackQuery.answer(queue_text, show_alert=True)


@app.on_callback_query(filters.regex("^aprogress\\|"))
@languageCB
async def autoplay_progress_callback(client, CallbackQuery, _):
    """Progress bar button - shows current time"""
    
    chat_id = int(CallbackQuery.data.split("|")[1])
    
    if chat_id in current_autoplay_track:
        track = current_autoplay_track[chat_id]
        current_sec = track.get("current_sec", 0)
        total_sec = track.get("duration_sec", 0)
        
        await CallbackQuery.answer(
            f"⏱ {format_time(current_sec)} / {format_time(total_sec)}",
            show_alert=False,
        )
    else:
        await CallbackQuery.answer("❌ ɴᴏ sᴏɴɢ ᴘʟᴀʏɪɴɢ", show_alert=False)


async def update_progress_bar(chat_id, message_id, total_duration, title, duration_str, thumbnail_url, mood, artist=""):
    """Update progress bar every 2 seconds with new image"""
    
    try:
        if chat_id not in current_autoplay_track:
            return
        
        start_time = time.time()
        last_update = 0
        
        while chat_id in current_autoplay_track:
            elapsed = int(time.time() - start_time)
            
            if elapsed > total_duration:
                break
            
            # Update track info
            current_autoplay_track[chat_id]["current_sec"] = elapsed
            
            # Update message every 2 seconds
            if elapsed - last_update >= 2:
                try:
                    if chat_id in progress_messages and message_id == progress_messages[chat_id]:
                        # Generate new thumbnail with updated progress
                        spotify_img = create_spotify_thumbnail_with_yt_image(
                            thumbnail_url,
                            title,
                            duration_str,
                            elapsed,
                            total_duration,
                            mood,
                            artist
                        )
                        
                        if spotify_img:
                            img_bytes = save_image_to_bytes(spotify_img)
                            
                            await app.edit_message_media(
                                chat_id=chat_id,
                                message_id=message_id,
                                media=await app.prepare_file(img_bytes)
                            )
                            
                            last_update = elapsed
                except Exception as e:
                    print(f"Progress Bar Update Error: {e}")
            
            await asyncio.sleep(1)
    
    except Exception as e:
        print(f"Progress Update Task Error: {e}")


async def process_autoplay_skip(chat_id, message):

    from Oneforall.core.call import Hotty

    autoplay_status = await is_autoplay_on(chat_id)

    if not autoplay_status:
        return await message.reply_text(
            "<blockquote>❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**</blockquote>"
        )

    try:
        track_data, track_id = await get_autoplay_recommendation(chat_id)

        if not track_data or not track_id:
            return await message.reply_text(
                "<blockquote>🦋 **ɴᴏ ɴᴇxᴛ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ ғᴏᴜɴᴅ**</blockquote>"
            )

        title = track_data.get("title", "Unknown")
        duration_str = track_data.get("duration", "Unknown")
        thumbnail_url = track_data.get("thumb", "")
        artist = track_data.get("artist", "")

        # Parse duration to seconds
        try:
            duration_parts = str(duration_str).split(":")
            if len(duration_parts) == 2:
                duration_sec = int(duration_parts[0]) * 60 + int(duration_parts[1])
            else:
                duration_sec = int(duration_parts[0])
        except:
            duration_sec = 0

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
                "<blockquote>❌ **ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ sᴏɴɢ**</blockquote>"
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
                "<blockquote>😭 **ғᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴀɴɢᴇ sᴛʀᴇᴀᴍ**</blockquote>"
            )

        try:
            # Get mood for Spotify thumbnail
            mood_data = await get_autoplay_mood(chat_id)
            mood = "chill"
            if isinstance(mood_data, dict):
                mood = mood_data.get("mood", "chill")
            
            # Generate Spotify-styled thumbnail with YouTube image
            spotify_img = create_spotify_thumbnail_with_yt_image(
                thumbnail_url,
                title,
                duration_str,
                0,  # current_sec
                duration_sec,  # total_sec
                mood,
                artist
            )
            
            if spotify_img:
                img_bytes = save_image_to_bytes(spotify_img)
                
                sent_message = await app.send_photo(
                    chat_id=chat_id,
                    photo=img_bytes,
                    caption=(
                        "<blockquote>⚙️ **𝐒ʈʀ𝛆ɑɱ𝛆ɗ 𝐀ᴜᴛ๏ᴘɭɑɣ 𝐒ᴋɩᴘᴘ𝛆ɗ ✮**</blockquote>"
                    ),
                    reply_markup=askip_markup(chat_id, 0, duration_sec),
                )
            else:
                # Fallback
                sent_message = await app.send_photo(
                    chat_id=chat_id,
                    photo=thumbnail_url if thumbnail_url else config.YOUTUBE_IMG_URL,
                    caption=(
                        "<blockquote>⚙️ **𝐒ʈʀ𝛆ɑɱ𝛆ɗ 𝐀ᴜᴛ๏ᴘɭɑɣ 𝐒ᴋɩᴘᴘ𝛆ɗ ✮**</blockquote>"
                    ),
                    reply_markup=askip_markup(chat_id, 0, duration_sec),
                )

            # Store current track info
            current_autoplay_track[chat_id] = {
                "title": title,
                "duration": duration_str,
                "duration_sec": duration_sec,
                "current_sec": 0,
                "vidid": track_id,
                "thumb": thumbnail_url,
            }
            
            progress_messages[chat_id] = sent_message.id
            
            # Cancel previous update task if exists
            if chat_id in update_tasks:
                try:
                    update_tasks[chat_id].cancel()
                except:
                    pass
            
            # Start progress bar update task
            update_tasks[chat_id] = asyncio.create_task(
                update_progress_bar(chat_id, sent_message.id, duration_sec, title, duration_str, thumbnail_url, mood, artist)
            )

        except Exception as e:
            print(f"Thumbnail Send Error: {e}")

    except Exception as e:
        print(f"Askip Error: {e}")

        return await message.reply_text(
            "<blockquote>❌ **ғᴀɪʟᴇᴅ ᴛᴏ sᴋɪᴘ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ**</blockquote>"
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
