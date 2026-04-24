from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from config import BANNED_USERS
from Oneforall import YouTube, app
from Oneforall.core.call import Hotty
from Oneforall.misc import db
from Oneforall.utils.database import get_loop
from Oneforall.utils.decorators import AdminRightsCheck
from Oneforall.utils.inline import close_markup, stream_markup, stream_markup2
from Oneforall.utils.stream.autoclear import auto_clean

PHOTO_URL = "https://graph.org/file/9bd106140750787f62681-320f969c2b6662e42a.jpg"


def skip_caption(app, videoid, title, dur, user):
    return f"""
╭━━━〔 ⏭️ 𝗦𝗞𝗜𝗣𝗣𝗘𝗗 〕━━━╮
┃ 🎵 **{title[:23]}**
┃ ⏱️ Duration: {dur}
┃ 👤 Requested by: {user}
╰━━━━━━━━━━━━━━━━━━━╯

✨ **Now Playing Next Track...**
🔗 **Powered by: @theteaminfinitynetwork**
"""


@app.on_message(
    filters.command(["skip", "cskip", "next", "cnext"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):

    # 🔹 MULTI SKIP LOGIC
    if not len(message.command) < 2:
        loop = await get_loop(chat_id)
        if loop != 0:
            return await message.reply_text(_["admin_8"])

        state = message.text.split(None, 1)[1].strip()

        if state.isnumeric():
            state = int(state)
            check = db.get(chat_id)

            if check:
                count = len(check)
                if count > 2:
                    count -= 1
                    if 1 <= state <= count:
                        for _ in range(state):
                            try:
                                popped = check.pop(0)
                                if popped:
                                    await auto_clean(popped)
                            except:
                                return await message.reply_text(_["admin_12"])

                            if not check:
                                await message.reply_text(
                                    text=_["admin_6"].format(
                                        message.from_user.mention,
                                        message.chat.title,
                                    ),
                                    reply_markup=close_markup(_),
                                )
                                try:
                                    await Hotty.stop_stream(chat_id)
                                except:
                                    pass
                                return
                    else:
                        return await message.reply_text(_["admin_11"].format(count))
                else:
                    return await message.reply_text(_["admin_10"])
            else:
                return await message.reply_text(_["queue_2"])
        else:
            return await message.reply_text(_["admin_9"])

    # 🔹 SINGLE SKIP
    else:
        check = db.get(chat_id)

        try:
            popped = check.pop(0)
            if popped:
                await auto_clean(popped)

            if not check:
                await message.reply_text(
                    text=_["admin_6"].format(
                        message.from_user.mention, message.chat.title
                    ),
                    reply_markup=close_markup(_),
                )
                return await Hotty.stop_stream(chat_id)

        except:
            await message.reply_text(
                text=_["admin_6"].format(
                    message.from_user.mention, message.chat.title
                ),
                reply_markup=close_markup(_),
            )
            return await Hotty.stop_stream(chat_id)

    # 🔹 NEXT TRACK
    queued = check[0]["file"]
    title = check[0]["title"].title()
    user = check[0]["by"]
    streamtype = check[0]["streamtype"]
    videoid = check[0]["vidid"]
    status = True if str(streamtype) == "video" else None

    db[chat_id][0]["played"] = 0

    # 🔹 LIVE STREAM
    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await message.reply_text(_["admin_7"].format(title))

        try:
            await Hotty.skip_stream(chat_id, link, video=status)
        except:
            return await message.reply_text(_["call_6"])

        # ✅ FIXED
        button = stream_markup2(_, chat_id)

        run = await message.reply_photo(
            photo=PHOTO_URL,
            caption=skip_caption(app, videoid, title, check[0]["dur"], user),
            reply_markup=button,  # ❌ no InlineKeyboardMarkup wrap
        )

        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    # 🔹 NORMAL STREAM
    else:
        try:
            await Hotty.skip_stream(chat_id, queued, video=status)
        except:
            return await message.reply_text(_["call_6"])

        # ✅ FIXED
        button = await stream_markup(_, videoid, chat_id)

        run = await message.reply_photo(
            photo=PHOTO_URL,
            caption=skip_caption(app, videoid, title, check[0]["dur"], user),
            reply_markup=button,  # ❌ no double wrap
        )

        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
