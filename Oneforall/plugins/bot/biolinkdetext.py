import re
import asyncio
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from motor.motor_asyncio import AsyncIOMotorClient

from Oneforall import app
from config import MONGO_URL, OTHER_LOGS, BOT_USERNAME

# ----------------- Mongo -----------------
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["OneForAll"]
col = db["BIO_LINK_FILTER"]

# ----------------- Regex -----------------
URL_PATTERN = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)
USERNAME_PATTERN = re.compile(r"@[\w_]+", re.IGNORECASE)

# ----------------- Cache -----------------
CACHE = {}

# ----------------- DB Functions -----------------
async def is_enabled(chat_id: int) -> bool:
    if chat_id in CACHE:
        return CACHE[chat_id]

    data = await col.find_one({"chat_id": chat_id})
    status = data.get("enabled", False) if data else False
    CACHE[chat_id] = status
    return status


async def set_enabled(chat_id: int, status: bool):
    CACHE[chat_id] = status
    await col.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )

# ----------------- Admin Check (FAST) -----------------
async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER
        ]
    except:
        return False

# ----------------- Command -----------------
@app.on_message(filters.command("biolink") & filters.group)
async def biolink_cmd(client, message):

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this.")

    if len(message.command) < 2:
        return await message.reply_text(
            "⚙️ **Usage:**\n`/biolink on`\n`/biolink off`"
        )

    arg = message.command[1].lower()

    if arg == "on":
        await set_enabled(message.chat.id, True)
        return await message.reply_text("✅ **Bio Link Filter Enabled**")

    elif arg == "off":
        await set_enabled(message.chat.id, False)
        return await message.reply_text("❌ **Bio Link Filter Disabled**")

    else:
        return await message.reply_text("Use: `/biolink on` or `/biolink off`")

# ----------------- Handler -----------------
@app.on_message(filters.group & filters.text)
async def bio_filter(client, message):

    chat_id = message.chat.id
    user = message.from_user

    if not user:
        return

    # Disabled
    if not await is_enabled(chat_id):
        return

    # Admin bypass
    if await is_admin(client, chat_id, user.id):
        return

    # ----------------- Get Bio -----------------
    try:
        user_info = await client.get_users(user.id)
        bio = user_info.bio or ""
    except:
        return

    if not bio:
        return

    # ----------------- Check -----------------
    if not (URL_PATTERN.search(bio) or USERNAME_PATTERN.search(bio)):
        return

    # ----------------- Action -----------------
    try:
        await message.delete()
    except:
        pass

    mention = f"[{user.first_name}](tg://user?id={user.id})"

    warn = await message.reply_text(
        f"⚠️ {mention}, **bio me link/username allowed nahi hai!**",
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close")]]
        )
    )

    await asyncio.sleep(8)
    try:
        await warn.delete()
    except:
        pass

    # ----------------- Logs -----------------
    log_text = f"""
🚨 **Bio Filter Triggered**

👤 User: {mention}
🆔 ID: `{user.id}`
💬 Chat: `{message.chat.title}`
📌 Bio: `{bio}`
"""

    try:
        await client.send_message(
            OTHER_LOGS,
            log_text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➕ Add Bot", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]]
            )
        )
    except:
        pass
