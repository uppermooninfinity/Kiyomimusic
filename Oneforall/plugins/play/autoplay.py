import random
import asyncio
import time
from datetime import datetime
from collections import defaultdict

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from pyrogram.enums import ButtonStyle

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

# Store autoplay queues per chat (unlimited)
autoplay_queues = defaultdict(list)
# Store progress update tasks per chat
progress_tasks = {}
# Store active autoplay messages for progress bar updates
autoplay_messages = {}
# Store track IDs to prevent exact duplicates within recent history
track_history = defaultdict(set)
# Maximum history to keep
MAX_HISTORY = 50
# Queue prefetch size
QUEUE_PREFETCH = 10


def build_progress_button(played_sec, total_sec):
    """Build a progress button text"""
    if total_sec == 0:
        percentage = 0
        filled = 0
    else:
        percentage = int((played_sec / total_sec) * 100)
        filled = int((played_sec / total_sec) * 10)
    
    bar = "█" * filled + "░" * (10 - filled)
    mins, secs = divmod(int(played_sec), 60)
    current_time = f"{mins:02d}:{secs:02d}"
    total_mins, total_secs = divmod(int(total_sec), 60)
    total_time = f"{total_mins:02d}:{total_secs:02d}"
    
    return f"{current_time} [{bar}] {total_time} {percentage}%"


def askip_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "sᴋɪᴘ",
                    callback_data="askip",
                    style=ButtonStyle.SUCCESS,
                ),
                InlineKeyboardButton(
                    "ᴄʟᴏsᴇ",
                    callback_data="autoplay_close",
                    style=ButtonStyle.DANGER,
                ),
            ]
        ]
    )


def askip_markup_with_progress(progress_text):
    """Create markup with progress bar as button"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    progress_text,
                    callback_data="progress_noop",
                ),
            ],
            [
                InlineKeyboardButton(
                    "sᴋɪᴘ",
                    callback_data="askip",
                    style=ButtonStyle.SUCCESS,
                ),
                InlineKeyboardButton(
                    "ᴄʟᴏsᴇ",
                    callback_data="autoplay_close",
                    style=ButtonStyle.DANGER,
                ),
            ]
        ]
    )


def autoplay_toggle_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ ᴇɴᴀʙʟᴇ",
                    callback_data="autoplay_enable",
                ),
                InlineKeyboardButton(
                    "❌ ᴅɪsᴀʙʟᴇ",
                    callback_data="autoplay_disable",
                ),
            ]
        ]
    )


async def update_progress_bar(chat_id, message_id, start_time, duration_sec, title, thumbnail):
    """Update progress bar periodically"""
    try:
        update_interval = 2  # Update every 2 seconds
        
        while True:
            if chat_id not in autoplay_messages:
                break
            
            elapsed = time.time() - start_time
            
            if elapsed >= duration_sec:
                # Song finished
                break
            
            progress_text = build_progress_button(elapsed, duration_sec)
            
            caption = (
                "<blockquote>⚙️ **𝐒ʈʀ𝛆ɑɱ𝛆ɗ 𝐀ᴜᴛ๏ᴘɭɑɣ 𝐏ʀ๏ɠʀєssɪɴɢ ✮**</blockquote>\n\n"
                f"<blockquote>🦋 **𝐍๏Ꮗ 𝐀ᴜᴛ๏ᴘɭɑɣɩŋʛ :** {title[:40]}</blockquote>\n"
                f"<blockquote><b>𝐏ɭᴜɠɪŋ 𝐃𝛆ᴠ𝛆ɭ๏ᴘ𝛆ɗ 𝐅ɩη𝛆ɭɣ 𝐁ɣ </b><a href='https://t.me/theinfinitynetwork'>˹𝐒η๏ᴡʏ 𝐍𝛆ʈᴡ๏ʀᴋ˼</a></blockquote>"
            )
            
            try:
                await app.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=caption,
                    reply_markup=askip_markup_with_progress(progress_text)
                )
            except Exception as e:
                print(f"Progress update error: {e}")
                break
            
            await asyncio.sleep(update_interval)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Progress bar error: {e}")
    finally:
        # Cleanup
        if chat_id in autoplay_messages:
            del autoplay_messages[chat_id]
        if chat_id in progress_tasks:
            del progress_tasks[chat_id]


async def prefetch_queue(chat_id):
    """Prefetch songs for the queue to keep it full"""
    try:
        while True:
            if chat_id not in autoplay_queues:
                await asyncio.sleep(5)
                continue
            
            # Keep queue stocked
            if len(autoplay_queues[chat_id]) < QUEUE_PREFETCH:
                try:
                    for _ in range(QUEUE_PREFETCH - len(autoplay_queues[chat_id])):
                        track_data, track_id = await get_autoplay_recommendation(chat_id)
                        if track_data and track_id:
                            autoplay_queues[chat_id].append({
                                "track_data": track_data,
                                "track_id": track_id
                            })
                except Exception as e:
                    print(f"Queue prefetch error: {e}")
            
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Prefetch error: {e}")


@app.on_message(filters.command("autoplay") & filters.group & ~BANNED_USERS)
@languageCB
async def autoplay_command(client, message, _):
    """Main autoplay toggle command"""
    
    chat_id = message.chat.id
    autoplay_status = await is_autoplay_on(chat_id)
    
    status_text = "✅ **ᴄᴜʀʀᴇɴᴛʟʏ ᴇɴᴀʙʟᴇᴅ**" if autoplay_status else "❌ **ᴄᴜʀʀᴇɴᴛʟʏ ᴅɪsᴀʙʟᴇᴅ**"
    
    await message.reply_text(
        f"🎵 **ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏɴᴛʀᴏʟ**\n\n{status_text}\n\n"
        "sᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ:",
        reply_markup=autoplay_toggle_markup(),
    )


@app.on_callback_query(filters.regex("autoplay_enable"))
@languageCB
async def autoplay_enable_callback(client, CallbackQuery, _):
    """Enable autoplay and show mood/language selection"""
    
    chat_id = CallbackQuery.message.chat.id
    
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass
    
    await CallbackQuery.message.reply_text(
        "🎵 **ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ**\n\n"
        "sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴏᴏᴅ:",
        reply_markup=autoplay_mood_markup(),
    )


@app.on_callback_query(filters.regex("autoplay_disable"))
@languageCB
async def autoplay_disable_callback(client, CallbackQuery, _):
    """Disable autoplay"""
    
    chat_id = CallbackQuery.message.chat.id
    
    await set_autoplay(chat_id, False)
    
    # Clear autoplay queue
    if chat_id in autoplay_queues:
        autoplay_queues[chat_id].clear()
    
    # Cancel progress tasks
    if chat_id in progress_tasks:
        try:
            progress_tasks[chat_id].cancel()
        except:
            pass
        del progress_tasks[chat_id]
    
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    try:
        await CallbackQuery.message.edit_reply_markup(None)
    except:
        pass
    
    await CallbackQuery.message.reply_text(
        "❌ **ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ**"
    )


@app.on_callback_query(filters.regex("progress_noop"))
async def progress_noop_callback(client, CallbackQuery):
    """No-op callback for progress button"""
    try:
        await CallbackQuery.answer()
    except:
        pass


@app.on_message(filters.command("mconfig") & filters.group & ~BANNED_USERS)
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
        
        # Clear queue
        if chat_id in autoplay_queues:
            autoplay_queues[chat_id].clear()

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


@app.on_callback_query(filters.regex("^autoplay_close$"))
async def autoplay_close_callback(client, CallbackQuery):
    """Handle autoplay close button"""
    
    chat_id = CallbackQuery.message.chat.id
    
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    # Cancel progress update task if exists
    if chat_id in progress_tasks:
        try:
            progress_tasks[chat_id].cancel()
        except:
            pass
        try:
            del progress_tasks[chat_id]
        except:
            pass
    
    try:
        await CallbackQuery.message.delete()
    except:
        pass


async def process_autoplay_skip(chat_id, message):

    from Oneforall.core.call import Hotty

    autoplay_status = await is_autoplay_on(chat_id)

    if not autoplay_status:
        try:
            return await message.reply_text(
                "❌ **ᴀᴜᴛᴏᴘʟᴀʏ ɪs ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ**"
            )
        except:
            pass
        return

    try:
        # Get next track from queue
        track_data, track_id = None, None
        
        if chat_id in autoplay_queues and len(autoplay_queues[chat_id]) > 0:
            queued = autoplay_queues[chat_id].pop(0)
            track_data = queued["track_data"]
            track_id = queued["track_id"]
        else:
            # Fetch a new one if queue is empty
            track_data, track_id = await get_autoplay_recommendation(chat_id)

        if not track_data or not track_id:
            try:
                return await message.reply_text(
                    "❌ **ɴᴏ ɴᴇxᴛ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ ғᴏᴜɴᴅ**"
                )
            except:
                pass
            return

        title = track_data.get("title", "Unknown")
        duration_min = track_data.get("duration", "Unknown")
        duration_sec = track_data.get("duration_sec", 0)
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
            try:
                return await message.reply_text(
                    "❌ **ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ sᴏɴɢ**"
                )
            except:
                pass
            return

        try:
            await Hotty.skip_stream(
                chat_id,
                file_path,
                video=None,
            )
        except Exception as e:
            print(f"Change Stream Error: {e}")
            try:
                return await message.reply_text(
                    "❌ **ғᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴀɴɢᴇ sᴛʀᴇᴀᴍ**"
                )
            except:
                pass
            return

        try:
            # Cancel previous progress task if exists
            if chat_id in progress_tasks:
                try:
                    progress_tasks[chat_id].cancel()
                except:
                    pass
                try:
                    del progress_tasks[chat_id]
                except:
                    pass
            
            # Send initial message with progress bar button
            initial_progress = build_progress_button(0, duration_sec)
            
            initial_caption = (
                "<blockquote>⚙️ **𝐒ʈʀ𝛆ɑɱ𝛆ɗ 𝐀ᴜᴛ๏ᴘɭɑɣ 𝐒ᴛᴀʀᴛɪɴɢ ✮**</blockquote>\n\n"
                f"<blockquote>🦋 **𝐍๏Ꮗ 𝐀ᴜᴛ๏ᴘɭɑɣɩŋʛ :** {title[:40]}</blockquote>\n"
                f"<blockquote><b>𝐏ɭᴜɠɪŋ 𝐃𝛆ᴠ𝛆ɭ๏ᴘ𝛆ɗ 𝐅ɩη𝛆ɭɣ 𝐁ɣ </b><a href='https://t.me/theinfinitynetwork'>˹𝐒η๏ᴡʏ 𝐍𝛆ʈᴡ๏ʀᴋ˼</a></blockquote>"
            )
            
            sent_message = await app.send_photo(
                chat_id=chat_id,
                photo=thumbnail if thumbnail else config.YOUTUBE_IMG_URL,
                caption=initial_caption,
                reply_markup=askip_markup_with_progress(initial_progress),
            )
            
            # Store message info for progress updates
            autoplay_messages[chat_id] = {
                "message_id": sent_message.id,
                "start_time": time.time(),
            }
            
            # Create and store progress update task
            if duration_sec > 0:
                progress_task = asyncio.create_task(
                    update_progress_bar(
                        chat_id,
                        sent_message.id,
                        time.time(),
                        duration_sec,
                        title[:40],
                        thumbnail
                    )
                )
                progress_tasks[chat_id] = progress_task

        except Exception as e:
            print(f"Thumbnail Send Error: {e}")

    except Exception as e:
        print(f"Askip Error: {e}")
        try:
            return await message.reply_text(
                "❌ **ғᴀɪʟᴇᴅ ᴛᴏ sᴋɪᴘ ᴀᴜᴛᴏᴘʟᴀʏ sᴏɴɢ**"
            )
        except:
            pass


async def get_autoplay_recommendation(chat_id: int):
    """Get next autoplay track with unlimited songs and no repetition"""

    mood_data = await get_autoplay_mood(chat_id)

    mood = "chill"
    language = "english"

    if isinstance(mood_data, dict):
        mood = mood_data.get("mood", "chill")
        language = mood_data.get("language", "english")

    # Get recent track history to avoid duplicates
    used_ids = track_history[chat_id]

    # Try to find a new track
    for attempt in range(15):
        try:
            # Fetch popular songs based on mood
            query = (
                f"{random.choice(['best', 'top', 'viral', 'popular', 'trending'])} "
                f"{language} {mood} songs"
            )

            track_data, track_id = await YouTube.track(query)

            if not track_data or not track_id:
                await asyncio.sleep(0.5)
                continue

            # Skip if already played recently
            if track_id in used_ids:
                await asyncio.sleep(0.5)
                continue

            # Parse duration
            duration_str = track_data.get("duration", "0:00")
            try:
                parts = duration_str.split(":")
                if len(parts) == 2:
                    duration_sec = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    duration_sec = 0
            except:
                duration_sec = 0

            track_data["duration_sec"] = duration_sec

            # Add to history (keep max 50 tracks)
            track_history[chat_id].add(track_id)
            if len(track_history[chat_id]) > MAX_HISTORY:
                # Remove oldest entries
                oldest = list(track_history[chat_id])[:len(track_history[chat_id]) - MAX_HISTORY]
                for old_id in oldest:
                    track_history[chat_id].discard(old_id)

            return track_data, track_id

        except Exception as e:
            print(f"Autoplay fetch attempt {attempt + 1} error: {e}")
            await asyncio.sleep(0.5)
            continue

    # If we can't find new songs, clear history and try again
    print(f"Clearing track history for chat {chat_id} to find new songs")
    track_history[chat_id].clear()
    
    try:
        query = (
            f"{random.choice(['best', 'top', 'viral', 'popular', 'trending'])} "
            f"{language} {mood} songs"
        )
        track_data, track_id = await YouTube.track(query)
        
        if track_data and track_id:
            # Parse duration
            duration_str = track_data.get("duration", "0:00")
            try:
                parts = duration_str.split(":")
                if len(parts) == 2:
                    duration_sec = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    duration_sec = 0
            except:
                duration_sec = 0

            track_data["duration_sec"] = duration_sec
            track_history[chat_id].add(track_id)
            return track_data, track_id
    except Exception as e:
        print(f"Final autoplay attempt error: {e}")

    return None, None
