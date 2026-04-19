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
from Oneforall.utils.thumbnails import get_thumb


PHOTO_URL = "https://graph.org/file/9bd106140750787f62681-320f969c2b6662e42a.jpg"   # 🔥 apna catbox link yaha daal


def skip_caption(app, videoid, title, dur, user):
    return f"""
╭━━━〔 ⏭️ 𝗦𝗞𝗜𝗣𝗣𝗘𝗗 〕━━━╮
┃ 🎵 **{title[:23]}**
┃ ⏱️ Duration: {dur}
┃ 👤 Requested by: {user}
╰━━━━━━━━━━━━━━━━━━━╯

✨ *Now Playing Next Track...*
🔗 *Powered by: @theteaminfinitynetwork
"""


@app.on_message(
    filters.command(["skip", "cskip", "next", "cnext"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
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
                    count = int(count - 1)
                    if 1 <= state <= count:
                        for x in range(state):
                            popped = None
                            try:
                                popped = check.pop(0)
                            except:
                                return await message.reply_text(_["admin_12"])
                            if popped:
                                await auto_clean(popped)
                            if not check:
                                try:
                                    await message.reply_text(
                                        text=_["admin_6"].format(
                                            message.from_user.mention,
                                            message.chat.title,
                                        ),
                                        reply_markup=close_markup(_),
                                    )
                                    await Hotty.stop_stream(chat_id)
                                except:
                                    return
                                break
                    else:
                        return await message.reply_text(_["admin_11"].format(count))
                else:
                    return await message.reply_text(_["admin_10"])
            else:
                return await message.reply_text(_["queue_2"])
        else:
            return await message.reply_text(_["admin_9"])
    else:
        check = db.get(chat_id)
        popped = None
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
                try:
                    return await Hotty.stop_stream(chat_id)
                except:
                    return
        except:
            try:
                await message.reply_text(
                    text=_["admin_6"].format(
                        message.from_user.mention, message.chat.title
                    ),
                    reply_markup=close_markup(_),
                )
                return await Hotty.stop_stream(chat_id)
            except:
                return

    queued = check[0]["file"]
    title = (check[0]["title"]).title()
    user = check[0]["by"]
    streamtype = check[0]["streamtype"]
    videoid = check[0]["vidid"]
    status = True if str(streamtype) == "video" else None

    db[chat_id][0]["played"] = 0

    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await message.reply_text(_["admin_7"].format(title))
        try:
            await Hotty.skip_stream(chat_id, link, video=status)
        except:
            return await message.reply_text(_["call_6"])

        button = stream_markup2(_, chat_id)

        run = await message.reply_photo(
            photo=PHOTO_URL,
            caption=skip_caption(app, videoid, title, check[0]["dur"], user),
            reply_markup=InlineKeyboardMarkup(button),
        )

        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    else:
        try:
            await Hotty.skip_stream(chat_id, queued, video=status)
        except:
            return await message.reply_text(_["call_6"])

        button = stream_markup(_, videoid, chat_id)

        run = await message.reply_photo(
            photo=PHOTO_URL,
            caption=skip_caption(app, videoid, title, check[0]["dur"], user),
            reply_markup=InlineKeyboardMarkup(button),
        )

        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
