import os
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from Oneforall import YouTube, app, Carbon
from Oneforall.core.call import Hotty

from Oneforall.misc import db
from Oneforall.utils.database import add_active_video_chat, is_active_chat
from Oneforall.utils.exceptions import AssistantErr
from Oneforall.utils.inline import (
    aq_markup,
    close_markup,
    stream_markup,
    stream_markup2,
)
from Oneforall.utils.stream.queue import put_queue, put_queue_index
from Oneforall.utils.thumbnails import get_thumb
from Oneforall.utils.stream.thumbnail import get_thumbnail_status


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):

    if not result:
        return

    intro_url = "https://graph.org/file/29d71d09801ca0ae55cd8-4832d851713ae41c8f.mp4"

    if forceplay:
        await Hotty.force_stop_stream(chat_id)

    # ===================== PLAYLIST =====================
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0

        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue

            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(
                    search, False if spotify else True
                )
            except:
                continue

            if str(duration_min) == "None":
                continue

            if duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )

            else:
                if not forceplay:
                    db[chat_id] = []

                status = True if video else None

                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except:
                    await mystic.edit_text(_["play_3"])

                thumb_on = get_thumbnail_status(chat_id) == "on"

                await Hotty.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=status,
                    image=thumbnail if thumb_on else None,
                )

                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path,
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )

                button = stream_markup(_, vidid, chat_id)

                if thumb_on:
                    run = await app.send_video(
                        original_chat_id,
                        video=config.YOUTUBE_VID_URL,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{vidid}",
                            title[:18],
                            duration_min,
                            user_name,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                else:
                    run = await app.send_message(
                        original_chat_id,
                        text=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{vidid}",
                            title[:18],
                            duration_min,
                            user_name,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        return

    # ===================== YOUTUBE =====================
    elif streamtype == "youtube":
        vidid = result["vidid"]
        title = result["title"].title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]

        status = True if video else None

        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, videoid=True, video=status
            )
        except:
            await mystic.edit_text(_["play_3"])

        if await is_active_chat(chat_id):

            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )

            button = aq_markup(_, chat_id)
            position = len(db.get(chat_id)) - 1

            thumb_on = get_thumbnail_status(chat_id) == "on"

            if thumb_on:
                await app.send_video(
                    chat_id=original_chat_id,
                    video=config.YOUTUBE_VID_URL,
                    caption=_["queue_4"].format(
                        position, title[:18], duration_min, user_name
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
            else:
                await app.send_message(
                    chat_id=original_chat_id,
                    text=_["queue_4"].format(
                        position, title[:18], duration_min, user_name
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )

        else:
            if not forceplay:
                db[chat_id] = []

            await Hotty.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail,
            )

            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )

            button = stream_markup(_, vidid, chat_id)
            thumb_on = get_thumbnail_status(chat_id) == "on"

            if thumb_on:
                run = await app.send_video(
                    original_chat_id,
                    video=config.YOUTUBE_VID_URL,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:18],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
            else:
                run = await app.send_message(
                    original_chat_id,
                    text=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:18],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
