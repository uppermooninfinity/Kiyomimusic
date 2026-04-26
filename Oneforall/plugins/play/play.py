import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery
from pyrogram.enums import ChatMemberStatus

from pytgcalls import PyTgCalls
from pytgcalls.exceptions import AlreadyJoinedError
from pytgcalls.types import MediaStream, AudioQuality
from pytgcalls.types.stream import StreamAudioEnded

from Oneforall import app
from config import API_ID, API_HASH, STRING_SESSION, BANNED_USERS

from Oneforall.platforms.Youtube import YouTubeAPI

yt = YouTubeAPI()

assistant = Client(
    "assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
)

call = PyTgCalls(assistant)

QUEUE = {}
AUTOPLAY = {}
PLAYING = {}

CMD = ["play", "skip", "stop", "end", "pause", "resume", "reload"]
PREFIX = ["/", "!", "."]


def cmd_filter(cmd):
    return filters.command(cmd, prefixes=PREFIX)


def buttons(chat_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸", callback_data=f"pause|{chat_id}"),
                InlineKeyboardButton("▶️", callback_data=f"resume|{chat_id}"),
                InlineKeyboardButton("⏭", callback_data=f"skip|{chat_id}"),
                InlineKeyboardButton("⏹", callback_data=f"stop|{chat_id}")
            ],
            [
                InlineKeyboardButton("🔁 autoplay", callback_data=f"autoplay|{chat_id}")
            ]
        ]
    )


async def is_admin(chat_id, user_id):
    member = await app.get_chat_member(chat_id, user_id)
    return member.status in [
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR
    ]


# ---------------- PLAY STREAM ----------------

async def play_stream(chat_id, mystic=None):

    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return

    data = QUEUE[chat_id][0]

    file, ok = await yt.download(data["link"], mystic)

    if not ok:
        return await app.send_message(chat_id, "❌ download failed")

    stream = MediaStream(
        file,
        audio_parameters=AudioQuality.HIGH
    )

    try:
        await call.join_group_call(chat_id, stream)
    except AlreadyJoinedError:
        await call.change_stream(chat_id, stream)

    PLAYING[chat_id] = data


# ---------------- PLAY COMMAND ----------------

@app.on_message(cmd_filter("play") & filters.group & ~BANNED_USERS)
async def play(_, message: Message):

    if len(message.command) < 2:
        return await message.reply_text("➻ ᴜsᴇ /play song")

    query = message.text.split(None, 1)[1]

    msg = await message.reply_photo(
        photo="https://graph.org/file/40f0822f02594343090cc-030776a6e3c7f31e9d.jpg",
        caption="➻ ᴘʀᴏᴄᴇssɪɴɢ..."
    )

    try:
        data, vidid = await yt.track(query)
    except:
        return await msg.edit_text("❌ error")

    chat_id = message.chat.id

    QUEUE.setdefault(chat_id, []).append(data)

    pos = len(QUEUE[chat_id])

    if pos == 1:
        await play_stream(chat_id, msg)

    caption = f"""
➻ ᴛɪᴛʟᴇ: {data['title']}
➻ ᴅᴜʀᴀᴛɪᴏɴ: {data['duration_min']}
➻ ᴘᴏsɪᴛɪᴏɴ: {pos}
➻ ʙʏ: {message.from_user.first_name}
"""

    await msg.edit_media(
        InputMediaPhoto(
            media=data["thumb"],
            caption=caption
        ),
        reply_markup=buttons(chat_id)
    )


# ---------------- SKIP ----------------

@app.on_message(cmd_filter("skip") & filters.group)
async def skip(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admins only")

    chat_id = message.chat.id

    if len(QUEUE.get(chat_id, [])) <= 1:
        return await message.reply_text("❌ no next song")

    QUEUE[chat_id].pop(0)
    await play_stream(chat_id)

    await message.reply_text("⏭ skipped")


# ---------------- STOP ----------------

@app.on_message(cmd_filter("stop") & filters.group)
async def stop(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admins only")

    chat_id = message.chat.id

    QUEUE[chat_id] = []
    await call.leave_group_call(chat_id)

    await message.reply_text("⏹ stopped")


# ---------------- END ----------------

@app.on_message(cmd_filter("end") & filters.group)
async def end(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admins only")

    chat_id = message.chat.id

    QUEUE[chat_id] = []
    await call.leave_group_call(chat_id)

    await message.reply_text("⏹ queue ended")


# ---------------- PAUSE ----------------

@app.on_message(cmd_filter("pause") & filters.group)
async def pause(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admins only")

    await call.pause_stream(message.chat.id)
    await message.reply_text("⏸ paused")


# ---------------- RESUME ----------------

@app.on_message(cmd_filter("resume") & filters.group)
async def resume(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admins only")

    await call.resume_stream(message.chat.id)
    await message.reply_text("▶️ resumed")


# ---------------- RELOAD ----------------

@app.on_message(cmd_filter("reload") & filters.group)
async def reload(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admins only")

    QUEUE.clear()
    AUTOPLAY.clear()
    PLAYING.clear()

    await message.reply_text("🔄 reloaded")


# ---------------- CALLBACKS ----------------

@app.on_callback_query(filters.regex("pause"))
async def cb_pause(_, q: CallbackQuery):
    await call.pause_stream(int(q.data.split("|")[1]))
    await q.answer("paused")


@app.on_callback_query(filters.regex("resume"))
async def cb_resume(_, q: CallbackQuery):
    await call.resume_stream(int(q.data.split("|")[1]))
    await q.answer("resumed")


@app.on_callback_query(filters.regex("skip"))
async def cb_skip(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])

    if len(QUEUE.get(chat_id, [])) <= 1:
        return await q.answer("no next", show_alert=True)

    QUEUE[chat_id].pop(0)
    await play_stream(chat_id)

    await q.answer("skipped")


@app.on_callback_query(filters.regex("stop"))
async def cb_stop(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])

    QUEUE[chat_id] = []
    await call.leave_group_call(chat_id)

    await q.answer("stopped")


@app.on_callback_query(filters.regex("autoplay"))
async def cb_autoplay(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])

    AUTOPLAY[chat_id] = not AUTOPLAY.get(chat_id, False)

    await q.answer(f"autoplay {'on' if AUTOPLAY[chat_id] else 'off'}")


# ---------------- STREAM END ----------------

@call.on_update()
async def stream_end(_, update):

    if not isinstance(update, StreamAudioEnded):
        return

    chat_id = update.chat_id

    if chat_id in QUEUE and QUEUE[chat_id]:
        QUEUE[chat_id].pop(0)

    if chat_id in QUEUE and QUEUE[chat_id]:
        await play_stream(chat_id)

    elif AUTOPLAY.get(chat_id):

        results = await yt.search("trending songs", limit=5)

        data = {
            "title": results[0]["title"],
            "duration_min": results[0]["duration"],
            "link": results[0]["link"],
            "thumb": results[0]["thumbnails"][0]["url"]
        }

        QUEUE.setdefault(chat_id, []).append(data)

        await play_stream(chat_id)

    else:
        await call.leave_group_call(chat_id)

        try:
            await app.send_message(chat_id, "➻ stream ended no queued chats !")
        except:
            pass


# ---------------- START ----------------

async def start():
    await assistant.start()
    await call.start()


asyncio.get_event_loop().run_until_complete(start())
