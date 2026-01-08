import random
import time
from typing import Dict, Tuple

from pyrogram import filters
from pyrogram.enums import ParseMode

from Oneforall import app
from Oneforall.mongo import db

# Collections
ECONOMY = db.roshni_economy
COOLDOWNS = db.roshni_cooldowns
INVENTORY = db.roshni_inventory

# -----------------------------
# Config (tune as you want)
# -----------------------------
DAILY_NORMAL = 1000
DAILY_PREMIUM = 2000

ROB_MAX_NORMAL = 10_000
ROB_MAX_PREMIUM = 100_000

ROB_COOLDOWN = 60 * 20         # 20 min
PROTECT_DURATION = 60 * 60 * 24 # 24 hours
PROTECT_COOLDOWN = 60 * 60 * 24 # 24 hours
GIFT_COOLDOWN = 60 * 60 * 12    # 12 hours

KILL_COST = 1000
REVIVE_SELF_COST = 2000
REVIVE_OTHER_COST = 2500
PROTECT_COST = 5000

# simple shop (optional usage inside /items)
SHOP: Dict[str, Dict[str, int]] = {
    "knife": {"price": 1500, "power": 1},
    "gun": {"price": 5000, "power": 2},
    "shield": {"price": 5000, "power": 0},  # alternative to /protect
    "revive_potion": {"price": 3000, "power": 0},
}

# -----------------------------
# Helpers
# -----------------------------
def _now() -> int:
    return int(time.time())

async def _ensure_user(uid: int):
    await ECONOMY.update_one(
        {"user_id": uid},
        {"$setOnInsert": {"user_id": uid, "balance": 0, "kills": 0, "deaths": 0, "is_dead": False}},
        upsert=True
    )
    await COOLDOWNS.update_one(
        {"user_id": uid},
        {"$setOnInsert": {"user_id": uid, "daily": 0, "rob": 0, "gift": 0, "protect_cd": 0, "shield_until": 0}},
        upsert=True
    )
    await INVENTORY.update_one(
        {"user_id": uid},
        {"$setOnInsert": {"user_id": uid, "items": {}}},
        upsert=True
    )

async def _get_user(uid: int) -> dict:
    await _ensure_user(uid)
    return await ECONOMY.find_one({"user_id": uid}) or {}

async def _get_cd(uid: int) -> dict:
    await _ensure_user(uid)
    return await COOLDOWNS.find_one({"user_id": uid}) or {}

async def _get_inv(uid: int) -> dict:
    await _ensure_user(uid)
    return await INVENTORY.find_one({"user_id": uid}) or {"items": {}}

async def _add_money(uid: int, amount: int):
    await _ensure_user(uid)
    await ECONOMY.update_one({"user_id": uid}, {"$inc": {"balance": int(amount)}})

async def _set_dead(uid: int, dead: bool):
    await _ensure_user(uid)
    await ECONOMY.update_one({"user_id": uid}, {"$set": {"is_dead": bool(dead)}})

async def _add_kill(uid: int):
    await _ensure_user(uid)
    await ECONOMY.update_one({"user_id": uid}, {"$inc": {"kills": 1}})

async def _add_death(uid: int):
    await _ensure_user(uid)
    await ECONOMY.update_one({"user_id": uid}, {"$inc": {"deaths": 1}})

async def _is_shielded(uid: int) -> Tuple[bool, int]:
    cd = await _get_cd(uid)
    until = int(cd.get("shield_until", 0) or 0)
    return (_now() < until), until

def _fmt_time_left(sec: int) -> str:
    if sec < 0:
        sec = 0
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"

async def _inv_add(uid: int, item: str, qty: int = 1):
    await _ensure_user(uid)
    await INVENTORY.update_one(
        {"user_id": uid},
        {"$inc": {f"items.{item}": int(qty)}},
        upsert=True
    )

async def _inv_take(uid: int, item: str, qty: int = 1) -> bool:
    inv = await _get_inv(uid)
    items = inv.get("items", {}) or {}
    have = int(items.get(item, 0) or 0)
    if have < qty:
        return False
    await INVENTORY.update_one({"user_id": uid}, {"$inc": {f"items.{item}": -int(qty)}})
    return True

def _premium(message) -> bool:
    u = message.from_user
    return bool(getattr(u, "is_premium", False))

# -----------------------------
# Commands: /bal
# -----------------------------
@app.on_message(filters.command(["bal", "balance"]))
async def roshni_bal(_, message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    data = await _get_user(target.id)
    bal = int(data.get("balance", 0) or 0)
    kills = int(data.get("kills", 0) or 0)
    dead = bool(data.get("is_dead", False))
    shielded, until = await _is_shielded(target.id)

    txt = (
        f"💳 **Roshni Wallet**

"
        f"👤 User: {target.mention}
"
        f"💰 Balance: `${bal:,}`
"
        f"⚔️ Kills: `{kills}`
"
        f"💀 Status: `{'DEAD' if dead else 'ALIVE'}`
"
        f"🛡️ Shield: `{'ON' if shielded else 'OFF'}`"
    )
    await message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)

# -----------------------------
# Commands: /daily, /claim
# -----------------------------
@app.on_message(filters.command(["daily", "claim"]))
async def roshni_daily(_, message):
    uid = message.from_user.id
    prem = _premium(message)
    cd = await _get_cd(uid)

    last = int(cd.get("daily", 0) or 0)
    now = _now()
    if now - last < 86400:
        left = 86400 - (now - last)
        return await message.reply_text(
            f"⏳ **Roshni says:** Come back in `{_fmt_time_left(left)}` for daily.",
            parse_mode=ParseMode.MARKDOWN
        )

    reward = DAILY_PREMIUM if prem else DAILY_NORMAL
    await _add_money(uid, reward)
    await COOLDOWNS.update_one({"user_id": uid}, {"$set": {"daily": now}}, upsert=True)

    await message.reply_text(
        f"🎁 **Daily Claimed!**
💰 You got `${reward:,}`{' (Premium)' if prem else ''}",
        parse_mode=ParseMode.MARKDOWN
    )

# -----------------------------
# Commands: /give (reply + amount)
# -----------------------------
@app.on_message(filters.command(["give"]))
async def roshni_give(_, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user: `/give 500`", parse_mode=ParseMode.MARKDOWN)
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/give <amount>` (reply to user)", parse_mode=ParseMode.MARKDOWN)

    try:
        amount = int(message.command[1])
    except Exception:
        return await message.reply_text("Amount must be a number.", parse_mode=ParseMode.MARKDOWN)

    if amount <= 0:
        return await message.reply_text("Amount must be > 0.", parse_mode=ParseMode.MARKDOWN)

    sender = message.from_user.id
    receiver = message.reply_to_message.from_user.id
    if sender == receiver:
        return await message.reply_text("Can't give money to yourself.", parse_mode=ParseMode.MARKDOWN)

    sdata = await _get_user(sender)
    sbal = int(sdata.get("balance", 0) or 0)
    if sbal < amount:
        return await message.reply_text("❌ Insufficient funds.", parse_mode=ParseMode.MARKDOWN)

    await _add_money(sender, -amount)
    await _add_money(receiver, amount)

    await message.reply_text(
        f"✅ Transfer complete.
"
        f"👤 From: {message.from_user.mention}
"
        f"👤 To: {message.reply_to_message.from_user.mention}
"
        f"💸 Amount: `${amount:,}`",
        parse_mode=ParseMode.MARKDOWN
    )

# -----------------------------
# Premium-only: /pay (same as give but premium required)
# -----------------------------
@app.on_message(filters.command(["pay"]))
async def roshni_pay(_, message):
    if not _premium(message):
        return await message.reply_text("💖 `/pay` is for Telegram Premium users only.", parse_mode=ParseMode.MARKDOWN)

    # Same behavior as /give
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user: `/pay 500`", parse_mode=ParseMode.MARKDOWN)
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/pay <amount>` (reply to user)", parse_mode=ParseMode.MARKDOWN)

    try:
        amount = int(message.command[1])
    except Exception:
        return await message.reply_text("Amount must be a number.", parse_mode=ParseMode.MARKDOWN)

    if amount <= 0:
        return await message.reply_text("Amount must be > 0.", parse_mode=ParseMode.MARKDOWN)

    sender = message.from_user.id
    receiver = message.reply_to_message.from_user.id
    if sender == receiver:
        return await message.reply_text("Can't pay yourself.", parse_mode=ParseMode.MARKDOWN)

    sbal = int((await _get_user(sender)).get("balance", 0) or 0)
    if sbal < amount:
        return await message.reply_text("❌ Insufficient funds.", parse_mode=ParseMode.MARKDOWN)

    await _add_money(sender, -amount)
    await _add_money(receiver, amount)
    await message.reply_text(f"💖 Premium payment sent: `${amount:,}`", parse_mode=ParseMode.MARKDOWN)

# -----------------------------
# Commands: /protect (shield 24h)
# -----------------------------
@app.on_message(filters.command(["protect"]))
async def roshni_protect(_, message):
    uid = message.from_user.id
    cd = await _get_cd(uid)
    now = _now()

    last = int(cd.get("protect_cd", 0) or 0)
    if now - last < PROTECT_COOLDOWN:
        left = PROTECT_COOLDOWN - (now - last)
        return await message.reply_text(
            f"⏳ Protect cooldown: `{_fmt_time_left(left)}`",
            parse_mode=ParseMode.MARKDOWN
        )

    data = await _get_user(uid)
    bal = int(data.get("balance", 0) or 0)
    if bal < PROTECT_COST:
        return await message.reply_text(f"❌ Protect costs `${PROTECT_COST:,}`.", parse_mode=ParseMode.MARKDOWN)

    await _add_money(uid, -PROTECT_COST)
    await COOLDOWNS.update_one(
        {"user_id": uid},
        {"$set": {"shield_until": now + PROTECT_DURATION, "protect_cd": now}},
        upsert=True
    )
    await message.reply_text("🛡️ Shield enabled for **24 hours**.", parse_mode=ParseMode.MARKDOWN)

# -----------------------------
# Commands: /rob (reply)
# -----------------------------
@app.on_message(filters.command(["rob"]))
async def roshni_rob(_, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to rob them.", parse_mode=ParseMode.MARKDOWN)

    robber = message.from_user.id
    victim = message.reply_to_message.from_user.id
    if robber == victim:
        return

    # cooldown
    cd = await _get_cd(robber)
    now = _now()
    last = int(cd.get("rob", 0) or 0)
    if now - last < ROB_COOLDOWN:
        left = ROB_COOLDOWN - (now - last)
        return await message.reply_text(
            f"⏳ Rob cooldown: `{_fmt_time_left(left)}`",
            parse_mode=ParseMode.MARKDOWN
        )

    # dead check
    rdata = await _get_user(robber)
    vdata = await _get_user(victim)
    if bool(rdata.get("is_dead", False)):
        return await message.reply_text("💀 You are dead. Use `/revive` first.", parse_mode=ParseMode.MARKDOWN)
    if bool(vdata.get("is_dead", False)):
        return await message.reply_text("💀 You can't rob a dead user.", parse_mode=ParseMode.MARKDOWN)

    # victim shield
    shielded, _ = await _is_shielded(victim)
    if shielded:
        await COOLDOWNS.update_one({"user_id": robber}, {"$set": {"rob": now}}, upsert=True)
        return await message.reply_text("🛡️ Rob failed: target is protected!", parse_mode=ParseMode.MARKDOWN)

    prem = _premium(message)
    limit = ROB_MAX_PREMIUM if prem else ROB_MAX_NORMAL

    vbal = int(vdata.get("balance", 0) or 0)
    if vbal < 500:
        await COOLDOWNS.update_one({"user_id": robber}, {"$set": {"rob": now}}, upsert=True)
        return await message.reply_text("Target is too poor to rob.", parse_mode=ParseMode.MARKDOWN)

    success_chance = 50 if prem else 40
    roll = random.randint(1, 100)

    await COOLDOWNS.update_one({"user_id": robber}, {"$set": {"rob": now}}, upsert=True)

    if roll <= success_chance:
        raw = random.randint(200, max(200, int(vbal * 0.35)))
        stolen = min(raw, limit, vbal)
        await _add_money(robber, stolen)
        await _add_money(victim, -stolen)
        return await message.reply_text(
            f"🎯 Success! You stole `${stolen:,}` from {message.reply_to_message.from_user.mention}",
            parse_mode=ParseMode.MARKDOWN
        )

    fine = 500
    await _add_money(robber, -fine)
    await message.reply_text(f"👮 Caught! Fine: `${fine:,}`", parse_mode=ParseMode.MARKDOWN)

# -----------------------------
# Commands: /kill (reply)
# -----------------------------
@app.on_message(filters.command(["kill"]))
async def roshni_kill(_, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to someone: `/kill`", parse_mode=ParseMode.MARKDOWN)

    killer = message.from_user.id
    victim = message.reply_to_message.from_user.id
    if killer == victim:
        return

    kdata = await _get_user(killer)
    vdata = await _get_user(victim)

    if bool(kdata.get("is_dead", False)):
        return await message.reply_text("💀 You are dead. Use `/revive` first.", parse_mode=ParseMode.MARKDOWN)
    if bool(vdata.get("is_dead", False)):
        return await message.reply_text("💀 Target is already dead.", parse_mode=ParseMode.MARKDOWN)

    shielded, _ = await _is_shielded(victim)
    if shielded:
        return await message.reply_text("🛡️ Kill failed: target is protected!", parse_mode=ParseMode.MARKDOWN)

    bal = int(kdata.get("balance", 0) or 0)
    if bal < KILL_COST:
        return await message.reply_text(f"❌ Killing costs `${KILL_COST:,}`.", parse_mode=ParseMode.MARKDOWN)

    await _add_money(killer, -KILL_COST)
    await _set_dead(victim, True)
    await _add_kill(killer)
    await _add_death(victim)

    await message.reply_text(
        f"💀 {message.reply_to_message.from_user.mention} was killed by {message.from_user.mention}!",
        parse_mode=ParseMode.MARKDOWN
    )

# -----------------------------
# Commands: /revive (self OR reply to revive other)
# -----------------------------
@app.on_message(filters.command(["revive"]))
async def roshni_revive(_, message):
    actor = message.from_user.id
    target = message.reply_to_message.from_user.id if message.reply_to_message else actor

    adata = await _get_user(actor)
    tdata = await _get_user(target)

    if not bool(tdata.get("is_dead", False)):
        return await message.reply_text("Target is already alive.", parse_mode=ParseMode.MARKDOWN)

    cost = REVIVE_OTHER_COST if target != actor else REVIVE_SELF_COST
    bal = int(adata.get("balance", 0) or 0)
    if bal < cost:
        return await message.reply_text(f"❌ Revive costs `${cost:,}`.", parse_mode=ParseMode.MARKDOWN)

    await _add_money(actor, -cost)
    await _set_dead(target, False)

    if target == actor:
        return await message.reply_text(f"😇 Roshni revived {message.from_user.mention}!", parse_mode=ParseMode.MARKDOWN)
    return await message.reply_text(
        f"😇 {message.from_user.mention} revived {message.reply_to_message.from_user.mention}!",
        parse_mode=ParseMode.MARKDOWN
    )

# -----------------------------
# Commands: /items (inventory + shop)
# -----------------------------
@app.on_message(filters.command(["items"]))
async def roshni_items(_, message):
    uid = message.from_user.id
    inv = await _get_inv(uid)
    items = inv.get("items", {}) or {}

    inv_lines = []
    for k, v in items.items():
        if int(v) > 0:
            inv_lines.append(f"• `{k}` x`{int(v)}`")
    inv_txt = "
".join(inv_lines) if inv_lines else "_Empty_"

    shop_lines = [f"• `{name}` — `${meta['price']:,}`" for name, meta in SHOP.items()]
    shop_txt = "
".join(shop_lines)

    await message.reply_text(
        "🎒 **Roshni Inventory**
"
        f"{inv_txt}

"
        "🛒 **Shop (info only)**
"
        f"{shop_txt}

"
        "Tip: `/gift` gives free items sometimes.",
        parse_mode=ParseMode.MARKDOWN
    )

# -----------------------------
# Commands: /gift (crate)
# -----------------------------
@app.on_message(filters.command(["gift"]))
async def roshni_gift(_, message):
    uid = message.from_user.id
    prem = _premium(message)
    cd = await _get_cd(uid)
    now = _now()

    last = int(cd.get("gift", 0) or 0)
    if now - last < GIFT_COOLDOWN:
        left = GIFT_COOLDOWN - (now - last)
        return await message.reply_text(
            f"⏳ Gift cooldown: `{_fmt_time_left(left)}`",
            parse_mode=ParseMode.MARKDOWN
        )

    await COOLDOWNS.update_one({"user_id": uid}, {"$set": {"gift": now}}, upsert=True)

    # premium gets slightly better odds
    money_min, money_max = (700, 2500) if prem else (300, 1500)
    money = random.randint(money_min, money_max)
    await _add_money(uid, money)

    # chance for an item
    item_roll = random.randint(1, 100)
    got_item = None
    if item_roll <= (45 if prem else 30):
        got_item = random.choice(list(SHOP.keys()))
        await _inv_add(uid, got_item, 1)

    txt = f"🎁 **Roshni Gift Crate!**
💰 Money: `${money:,}`"
    if got_item:
        txt += f"
🎒 Item: `{got_item}` x`1`"
    txt += f"
{'💖 Premium bonus applied' if prem else ''}"

    await message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)

# -----------------------------
# Commands: /toprich, /topkill
# -----------------------------
@app.on_message(filters.command(["toprich"]))
async def roshni_toprich(_, message):
    cursor = ECONOMY.find({}).sort("balance", -1).limit(10)
    lines = []
    i = 1
    async for u in cursor:
        lines.append(f"{i}. `{u.get('user_id')}` — `${int(u.get('balance', 0) or 0):,}`")
        i += 1
    text = "👑 **ROSHNI TOP RICH**

" + ("
".join(lines) if lines else "_No data yet_")
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command(["topkill"]))
async def roshni_topkill(_, message):
    cursor = ECONOMY.find({}).sort("kills", -1).limit(10)
    lines = []
    i = 1
    async for u in cursor:
        lines.append(f"{i}. `{u.get('user_id')}` — ⚔️ `{int(u.get('kills', 0) or 0)}`")
        i += 1
    text = "⚔️ **ROSHNI TOP KILLS**

" + ("
".join(lines) if lines else "_No data yet_")
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
