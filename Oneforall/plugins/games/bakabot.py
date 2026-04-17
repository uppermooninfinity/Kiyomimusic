import random
import asyncio
import time
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from Oneforall.utils import (
    ensure_user_exists,
    resolve_target,
    get_active_protection,
    format_time,
    get_mention
)
from Oneforall.utils.database import users_collection

# ---------------- CONFIG ---------------- #

COOLDOWN = {}
COOLDOWN_TIME = 30
user_last_msg = {}

# ---------------- LEAGUE ---------------- #

def get_league(msgs):
    if msgs >= 10000:
        return "💎 ᴅɪᴀᴍᴏɴᴅ"
    elif msgs >= 5000:
        return "🏆 ᴘʟᴀᴛɪɴᴜᴍ"
    elif msgs >= 2000:
        return "🥇 ɢᴏʟᴅ"
    elif msgs >= 1000:
        return "🥈 sɪʟᴠᴇʀ"
    elif msgs >= 500:
        return "🥉 ʙʀᴏɴᴢᴇ"
    else:
        return "👶 ɴᴇᴡʙɪᴇ"

# ---------------- WATCHER (ANTI SPAM) ---------------- #

async def message_watcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return

    user_id = update.message.from_user.id
    name = update.message.from_user.first_name

    now = time.time()
    last = user_last_msg.get(user_id, 0)
    user_last_msg[user_id] = now

    score = 0.2 if now - last < 2 else 1

    users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "total_messages": score,
                "weekly": score,
                "monthly": score
            },
            "$set": {"name": name}
        },
        upsert=True
    )

# ---------------- KILL ---------------- #

async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):

    attacker = ensure_user_exists(update.effective_user)
    target, _ = await resolve_target(update, context)

    if not target:
        return await update.message.reply_text("⚠️ /kill @user")

    if attacker['status'] == 'dead':
        return await update.message.reply_text("💀 You are dead")

    if target['status'] == 'dead':
        return await update.message.reply_text("⚰️ Already dead")

    if target['user_id'] == attacker['user_id']:
        return await update.message.reply_text("🤡 No")

    now = time.time()
    if now - COOLDOWN.get(attacker["user_id"], 0) < COOLDOWN_TIME:
        return await update.message.reply_text("⏳ Wait 30 sec")

    COOLDOWN[attacker["user_id"]] = now

    expiry = get_active_protection(target)
    if expiry:
        rem = expiry - datetime.utcnow()
        return await update.message.reply_text(f"🛡️ Safe {format_time(rem)}")

    reward = random.randint(100, 200)

    users_collection.update_one(
        {"user_id": target["user_id"]},
        {"$set": {"status": "dead", "death_time": datetime.utcnow()}}
    )

    users_collection.update_one(
        {"user_id": attacker["user_id"]},
        {"$inc": {
            "kills": 1,
            "coins": reward,
            "total_messages": 5,
            "weekly": 5,
            "monthly": 5
        }},
        upsert=True
    )

    await update.message.reply_text(f"🔪 Kill success 💰 +{reward}")

# ---------------- ROB ---------------- #

async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):

    attacker = ensure_user_exists(update.effective_user)

    if len(context.args) < 2:
        return await update.message.reply_text("⚠️ /rob amount @user")

    amount = int(context.args[0])
    target, _ = await resolve_target(update, context)

    if not target:
        return

    if target.get("coins", 0) < amount:
        return await update.message.reply_text("💸 Poor target")

    users_collection.update_one(
        {"user_id": target["user_id"]},
        {"$inc": {"coins": -amount}}
    )

    users_collection.update_one(
        {"user_id": attacker["user_id"]},
        {"$inc": {
            "coins": amount,
            "total_messages": 2,
            "weekly": 2,
            "monthly": 2
        }},
        upsert=True
    )

    await update.message.reply_text(f"💰 robbed {amount}")

# ---------------- PROFILE ---------------- #

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    data = users_collection.find_one({"user_id": user_id})

    if not data:
        return await update.message.reply_text("No data")

    total = int(data.get("total_messages", 0))
    weekly = int(data.get("weekly", 0))
    monthly = int(data.get("monthly", 0))
    coins = data.get("coins", 0)
    kills = data.get("kills", 0)

    users = list(users_collection.find().sort("total_messages", -1))
    pos = next((i+1 for i,u in enumerate(users) if u["user_id"] == user_id), "N/A")

    league = get_league(total)

    text = f"""
👤 YOUR PROFILE

• Coins: {coins}
• Kills: {kills}

• Messages: {total}
• Weekly: {weekly}
• Monthly: {monthly}

• Rank: {pos}

{league}
"""
    await update.message.reply_text(text)

# ---------------- LEADERBOARD ---------------- #

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    top = users_collection.find().sort("total_messages", -1).limit(10)

    text = "🏆 LEADERBOARD\n\n"

    i = 1
    for u in top:
        name = u.get("name", "user")
        msgs = int(u.get("total_messages", 0))
        text += f"{i}. {name} ➤ {msgs}\n"
        i += 1

    await update.message.reply_text(text)

# ---------------- MONTHLY RESET ---------------- #

async def monthly_reset():
    while True:
        now = datetime.utcnow()
        if now.day == 1 and now.hour == 0:
            users_collection.update_many({}, {"$set": {"monthly": 0}})
        await asyncio.sleep(3600)

# ---------------- WEEKLY RESET ---------------- #

async def weekly_reset():
    while True:
        now = datetime.utcnow()
        if now.weekday() == 0 and now.hour == 0:
            users_collection.update_many({}, {"$set": {"weekly": 0}})
        await asyncio.sleep(3600)

# ---------------- AUTO REVIVE ---------------- #

async def auto_revive_loop():
    while True:
        now = datetime.utcnow()

        for u in users_collection.find({"status": "dead"}):
            dt = u.get("death_time")
            if dt and (now - dt).total_seconds() > 3600:
                users_collection.update_one(
                    {"user_id": u["user_id"]},
                    {"$set": {"status": "alive", "death_time": None}}
                )

        await asyncio.sleep(60)
