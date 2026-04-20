from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from datetime import datetime
from Oneforall import app
from Oneforall.utils.database import db

# ─── DATABASE KEYS ───
MARRIAGE_DB = "MARRIAGE_DATA"


# ─── HELP STRING ───
__HELP__ = """
✦ Marriage:

✧ /marry @username - Send marriage proposal with consent buttons.
✧ /marry (reply) - Send marriage proposal to replied user.
✧ /divorce @username - Send divorce request with consent buttons.
✧ /divorce (reply) - Send divorce request to replied user.
✧ /partner @username or reply - Show partner of user (defaults to you).
✧ /marriagestatus @username or reply - Show marriage date and together duration.
"""


# ─── UTILS ───
async def get_partner(user_id: int):
    data = await db.get(MARRIAGE_DB) or {}
    return data.get(str(user_id))


async def set_marriage(user1, user2):
    data = await db.get(MARRIAGE_DB) or {}
    now = datetime.utcnow().isoformat()

    data[str(user1)] = {"partner": user2, "since": now}
    data[str(user2)] = {"partner": user1, "since": now}

    await db.set(MARRIAGE_DB, data)


async def remove_marriage(user1, user2):
    data = await db.get(MARRIAGE_DB) or {}

    data.pop(str(user1), None)
    data.pop(str(user2), None)

    await db.set(MARRIAGE_DB, data)


# ─── MARRY COMMAND ───
@app.on_message(filters.command("marry") & filters.group)
async def marry_cmd(_, message: Message):
    user = message.from_user

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        if len(message.command) < 2:
            return await message.reply("❌ Give username or reply.")
        target = await app.get_users(message.command[1])

    if user.id == target.id:
        return await message.reply("💀 You can't marry yourself.")

    # Check already married
    if await get_partner(user.id):
        return await message.reply("❌ You're already married.")

    if await get_partner(target.id):
        return await message.reply("❌ That user is already married.")

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💍 Accept", callback_data=f"marry_accept|{user.id}|{target.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"marry_reject|{user.id}|{target.id}")
        ]
    ])

    await message.reply(
        f"💖 {user.mention} has proposed to {target.mention}!\n\nDo you accept?",
        reply_markup=buttons
    )


# ─── CALLBACKS ───
@app.on_callback_query(filters.regex("^marry_"))
async def marry_callback(_, query: CallbackQuery):
    data = query.data.split("|")
    action, sender_id, target_id = data[0], int(data[1]), int(data[2])

    user = query.from_user

    if user.id != target_id:
        return await query.answer("Not for you!", show_alert=True)

    if action == "marry_accept":
        await set_marriage(sender_id, target_id)
        await query.message.edit_text("💍 Marriage successful! ❤️")

    elif action == "marry_reject":
        await query.message.edit_text("❌ Proposal rejected.")


# ─── DIVORCE ───
@app.on_message(filters.command("divorce") & filters.group)
async def divorce_cmd(_, message: Message):
    user = message.from_user

    partner_data = await get_partner(user.id)
    if not partner_data:
        return await message.reply("❌ You're not married.")

    partner_id = partner_data["partner"]

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💔 Accept Divorce", callback_data=f"div_accept|{user.id}|{partner_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"div_reject|{user.id}|{partner_id}")
        ]
    ])

    await message.reply("💔 Divorce request sent.", reply_markup=buttons)


@app.on_callback_query(filters.regex("^div_"))
async def divorce_callback(_, query: CallbackQuery):
    data = query.data.split("|")
    action, sender_id, partner_id = data[0], int(data[1]), int(data[2])

    user = query.from_user

    if user.id != partner_id:
        return await query.answer("Not for you!", show_alert=True)

    if action == "div_accept":
        await remove_marriage(sender_id, partner_id)
        await query.message.edit_text("💔 Divorce completed.")

    elif action == "div_reject":
        await query.message.edit_text("❌ Divorce cancelled.")


# ─── PARTNER ───
@app.on_message(filters.command("partner") & filters.group)
async def partner_cmd(_, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user = await app.get_users(message.command[1])
    else:
        user = message.from_user

    data = await get_partner(user.id)

    if not data:
        return await message.reply("❌ No partner found.")

    partner = await app.get_users(data["partner"])
    await message.reply(f"💑 Partner: {partner.mention}")


# ─── STATUS ───
@app.on_message(filters.command("marriagestatus") & filters.group)
async def status_cmd(_, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user = await app.get_users(message.command[1])
    else:
        user = message.from_user

    data = await get_partner(user.id)

    if not data:
        return await message.reply("❌ Not married.")

    partner = await app.get_users(data["partner"])
    since = datetime.fromisoformat(data["since"])
    now = datetime.utcnow()

    duration = now - since
    days = duration.days

    await message.reply(
        f"💍 {user.mention} ❤️ {partner.mention}\n"
        f"📅 Married since: {since.date()}\n"
        f"⏳ Together: {days} days"
  )
