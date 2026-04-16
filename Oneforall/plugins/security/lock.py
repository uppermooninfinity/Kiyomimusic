import re
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pymongo import MongoClient

from Oneforall import app
from config import MONGO_DB_URI

mongo = MongoClient(MONGO_DB_URI)
db = mongo["musicbot"]
locks_db = db["locks"]

LOCK_CACHE = {}

LOCKS = {
    "all": "ʟᴏᴄᴋ ᴇᴠᴇʀʏᴛʜɪɴɢ",
    "album": "ʙʟᴏᴄᴋ ᴀʟʙᴜᴍs",
    "anonchannel": "ʙʟᴏᴄᴋ ᴀɴᴏɴ ᴘᴏsᴛs",
    "audio": "ʙʟᴏᴄᴋ ᴀᴜᴅɪᴏ",
    "bot": "ʙʟᴏᴄᴋ ʙᴏᴛs",
    "botlink": "ʙʟᴏᴄᴋ ʙᴏᴛ ʟɪɴᴋs",
    "button": "ʙʟᴏᴄᴋ ʙᴜᴛᴛᴏɴs",
    "cashtag": "ʙʟᴏᴄᴋ $ᴛᴀɢs",
    "checklist": "ʙʟᴏᴄᴋ ᴄʜᴇᴄᴋʟɪsᴛ",
    "cjk": "ʙʟᴏᴄᴋ ᴄᴊᴋ",
    "command": "ʙʟᴏᴄᴋ /ᴄᴏᴍᴍᴀɴᴅs",
    "comment": "ʙʟᴏᴄᴋ ᴄᴏᴍᴍᴇɴᴛs",
    "contact": "ʙʟᴏᴄᴋ ᴄᴏɴᴛᴀᴄᴛs",
    "cyrillic": "ʙʟᴏᴄᴋ ᴄʏʀɪʟʟɪᴄ",
    "document": "ʙʟᴏᴄᴋ ғɪʟᴇs",
    "email": "ʙʟᴏᴄᴋ ᴇᴍᴀɪʟs",
    "emoji": "ʙʟᴏᴄᴋ ᴇᴍᴏᴊɪ",
    "emojicustom": "ʙʟᴏᴄᴋ ᴄᴜsᴛᴏᴍ",
    "emojigame": "ʙʟᴏᴄᴋ ɢᴀᴍᴇ",
    "emojionly": "ᴏɴʟʏ ᴇᴍᴏᴊɪ",
    "externalreply": "ʙʟᴏᴄᴋ ʀᴇᴘʟʏ",
    "forward": "ʙʟᴏᴄᴋ ғᴏʀᴡᴀʀᴅ",
    "forwardbot": "ʙʟᴏᴄᴋ ғʙᴏᴛ",
    "forwardchannel": "ʙʟᴏᴄᴋ ғᴄʜ",
    "forwardstory": "ʙʟᴏᴄᴋ ғsᴛᴏʀʏ",
    "forwarduser": "ʙʟᴏᴄᴋ ғᴜsᴇʀ",
    "game": "ʙʟᴏᴄᴋ ɢᴀᴍᴇs",
    "gif": "ʙʟᴏᴄᴋ ɢɪғ",
    "inline": "ʙʟᴏᴄᴋ ɪɴʟɪɴᴇ",
    "invitelink": "ʙʟᴏᴄᴋ ɪɴᴠɪᴛᴇ",
    "location": "ʙʟᴏᴄᴋ ʟᴏᴄ",
    "phone": "ʙʟᴏᴄᴋ ᴘʜᴏɴᴇ",
    "photo": "ʙʟᴏᴄᴋ ᴘʜᴏᴛᴏ",
    "poll": "ʙʟᴏᴄᴋ ᴘᴏʟʟ",
    "rtl": "ʙʟᴏᴄᴋ ʀᴛʟ",
    "spoiler": "ʙʟᴏᴄᴋ sᴘᴏɪʟᴇʀ",
    "sticker": "ʙʟᴏᴄᴋ sᴛɪᴄᴋᴇʀ",
    "stickeranimated": "ʙʟᴏᴄᴋ ᴀɴɪᴍ",
    "stickerpremium": "ʙʟᴏᴄᴋ ᴘʀᴇᴍ",
    "text": "ʙʟᴏᴄᴋ ᴛᴇxᴛ",
    "url": "ʙʟᴏᴄᴋ ʟɪɴᴋ",
    "video": "ʙʟᴏᴄᴋ ᴠɪᴅᴇᴏ",
    "videonote": "ʙʟᴏᴄᴋ ᴠɴ",
    "voice": "ʙʟᴏᴄᴋ ᴠᴏɪᴄᴇ",
    "zalgо": "ʙʟᴏᴄᴋ ᴢᴀʟɢᴏ"
}

# ---------------- ADMIN ---------------- #
async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False


# ---------------- DB ---------------- #
def get_locks(chat_id):
    if chat_id in LOCK_CACHE:
        return LOCK_CACHE[chat_id]

    data = locks_db.find_one({"chat_id": chat_id})
    locks = data["locks"] if data else []
    LOCK_CACHE[chat_id] = locks
    return locks


def save_locks(chat_id, locks):
    LOCK_CACHE[chat_id] = locks
    locks_db.update_one({"chat_id": chat_id}, {"$set": {"locks": locks}}, upsert=True)


# ---------------- COMMANDS ---------------- #

@app.on_message(filters.command(["lock", "locktypes"]) & filters.group)
async def locktypes(client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("Admins only")

    text = "🔐 **Available Lock Types:**\n\n"
    for key, val in LOCKS.items():
        text += f"• `{key}` → {val}\n"

    text += "\nUse:\n`/lock type`\n`/unlock type`"
    await message.reply(text)


@app.on_message(filters.command("locks") & filters.group)
async def current_locks(client, message: Message):
    locks = get_locks(message.chat.id)

    if not locks:
        return await message.reply("No locks enabled.")

    text = "🔒 **Current Locks:**\n\n"
    for l in locks:
        text += f"• `{l}`\n"

    await message.reply(text)


@app.on_message(filters.command("lock") & filters.group)
async def lock_cmd(client, message: Message):
    if len(message.command) == 1:
        return

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("Admins only")

    lock = message.command[1].lower()

    if lock not in LOCKS:
        return await message.reply("Invalid lock type")

    locks = get_locks(message.chat.id)

    if lock in locks:
        return await message.reply("Already locked")

    if lock == "all":
        locks = ["all"]
    else:
        if "all" in locks:
            locks.remove("all")
        locks.append(lock)

    save_locks(message.chat.id, locks)
    await message.reply(f"Locked `{lock}`")


@app.on_message(filters.command("unlock") & filters.group)
async def unlock_cmd(client, message: Message):
    if len(message.command) == 1:
        return

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("Admins only")

    lock = message.command[1].lower()

    if lock == "all":
        save_locks(message.chat.id, [])
        return await message.reply("All locks removed")

    locks = get_locks(message.chat.id)

    if lock not in locks:
        return await message.reply("Not locked")

    locks.remove(lock)
    save_locks(message.chat.id, locks)

    await message.reply(f"Unlocked `{lock}`")


# ---------------- ENFORCE ---------------- #
@app.on_message(filters.group, group=1)
async def enforce(client, message: Message):

    if message.text and message.text.startswith("/"):
        return

    locks = get_locks(message.chat.id)

    if message.from_user and await is_admin(client, message.chat.id, message.from_user.id):
        return

    try:
        text = message.text or message.caption or ""

        if "all" in locks:
            return await message.delete()

        if "photo" in locks and message.photo:
            return await message.delete()

        if "video" in locks and message.video:
            return await message.delete()

        if "gif" in locks and message.animation:
            return await message.delete()

        if "sticker" in locks and message.sticker:
            return await message.delete()

        if "voice" in locks and message.voice:
            return await message.delete()

        if "audio" in locks and message.audio:
            return await message.delete()

        if "document" in locks and message.document:
            return await message.delete()

        if "url" in locks and re.search(r"(https?://|www\.)", text):
            return await message.delete()

        if "text" in locks and message.text:
            return await message.delete()

    except:
        pass
