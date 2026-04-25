import asyncio
import random
import requests
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import Message, InlineQuery, InlineQueryResultPhoto
from Oneforall import app
from pymongo import MongoClient

mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["waifu_game"]

waifu_col = db["waifus"]
user_col = db["users"]
group_col = db["groups"]

JIKAN = "https://api.jikan.moe/v4"

RARITY_REWARD = {
    "UR": 800,
    "SSR": 300,
    "SR": 120,
    "R": 50
}

def sc(t):
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    return "".join([small[normal.index(c)] if c in normal else c for c in t.lower()])

def rarity():
    r = random.randint(1, 100)
    if r <= 1:
        return "UR"
    elif r <= 5:
        return "SSR"
    elif r <= 20:
        return "SR"
    return "R"

def fetch():
    aid = random.randint(1, 500)
    try:
        a = requests.get(f"{JIKAN}/anime/{aid}").json()["data"]
        c = requests.get(f"{JIKAN}/anime/{aid}/characters").json()["data"]
    except:
        return None

    if not c:
        return None

    ch = random.choice(c)["character"]

    return {
        "mal_id": ch["mal_id"],
        "name": ch["name"],
        "image": ch["images"]["jpg"]["image_url"],
        "anime": a["title"],
        "rarity": rarity(),
        "claimed": False,
        "claimed_by": None,
        "chat_id": None,
        "price": random.randint(100, 1000),
        "created_at": datetime.utcnow()
    }

async def drop(chat_id):
    w = fetch()
    if not w:
        return

    w["chat_id"] = chat_id
    waifu_col.insert_one(w)

    txt = f"""
💖 {sc('waifu appeared')}

{sc('name')}: {w['name']}
{sc('anime')}: {w['anime']}
{sc('rarity')}: {w['rarity']}

{sc('claim')}: /claim {w['mal_id']}
"""

    await app.send_photo(chat_id, w["image"], caption=txt)

async def auto_drop():
    while True:
        groups = group_col.find({"enabled": True})
        for g in groups:
            try:
                await drop(g["chat_id"])
                await asyncio.sleep(2)
            except:
                pass
        await asyncio.sleep(600)

@app.on_message(filters.command("startdrops") & filters.group)
async def start(_, m: Message):
    group_col.update_one(
        {"chat_id": m.chat.id},
        {"$set": {"enabled": True}},
        upsert=True
    )
    await m.reply(sc("drops enabled"))

@app.on_message(filters.command("stopdrops") & filters.group)
async def stop(_, m: Message):
    group_col.update_one(
        {"chat_id": m.chat.id},
        {"$set": {"enabled": False}}
    )
    await m.reply(sc("drops disabled"))

@app.on_message(filters.command("claim"))
async def claim(_, m: Message):
    if len(m.command) < 2:
        return await m.reply(sc("usage /claim id"))

    mid = int(m.command[1])

    w = waifu_col.find_one({
        "mal_id": mid,
        "claimed": False,
        "chat_id": m.chat.id
    })

    if not w:
        return await m.reply(sc("not available"))

    rew = RARITY_REWARD.get(w["rarity"], 50)

    waifu_col.update_one(
        {"_id": w["_id"]},
        {"$set": {"claimed": True, "claimed_by": m.from_user.id}}
    )

    user_col.update_one(
        {"user_id": m.from_user.id},
        {
            "$inc": {"coins": rew},
            "$push": {"waifus": w},
            "$set": {"name": m.from_user.first_name}
        },
        upsert=True
    )

    await m.reply(sc(f"claimed {w['name']} +{rew} coins"))

@app.on_message(filters.command("balance"))
async def balance(_, m: Message):
    u = user_col.find_one({"user_id": m.from_user.id})
    coins = u.get("coins", 0) if u else 0
    await m.reply(sc(f"coins {coins}"))

@app.on_message(filters.command("harem"))
async def harem(_, m: Message):
    u = user_col.find_one({"user_id": m.from_user.id})

    if not u or not u.get("waifus"):
        return await m.reply(sc("no waifus"))

    txt = sc("your harem") + "\n\n"
    for w in u["waifus"][:20]:
        txt += f"{w['mal_id']} • {w['name']} ({w['rarity']})\n"

    await m.reply(txt)

@app.on_message(filters.command("shop"))
async def shop(_, m: Message):
    ws = list(waifu_col.find({"claimed": False}).limit(10))

    if not ws:
        return await m.reply(sc("shop empty"))

    txt = sc("shop") + "\n\n"
    for w in ws:
        txt += f"{w['mal_id']} • {w['name']} — {w['price']}\n"

    await m.reply(txt)

@app.on_message(filters.command("buy"))
async def buy(_, m: Message):
    mid = int(m.command[1])

    w = waifu_col.find_one({"mal_id": mid, "claimed": False})
    u = user_col.find_one({"user_id": m.from_user.id})

    if not w:
        return await m.reply(sc("not available"))

    coins = u.get("coins", 0) if u else 0

    if coins < w["price"]:
        return await m.reply(sc("not enough coins"))

    waifu_col.update_one(
        {"_id": w["_id"]},
        {"$set": {"claimed": True, "claimed_by": m.from_user.id}}
    )

    user_col.update_one(
        {"user_id": m.from_user.id},
        {
            "$inc": {"coins": -w["price"]},
            "$push": {"waifus": w}
        },
        upsert=True
    )

    await m.reply(sc(f"bought {w['name']}"))

@app.on_message(filters.command("sell"))
async def sell(_, m: Message):
    mid = int(m.command[1])
    u = user_col.find_one({"user_id": m.from_user.id})

    if not u:
        return await m.reply(sc("no waifus"))

    w = None
    for i in u.get("waifus", []):
        if i["mal_id"] == mid:
            w = i
            break

    if not w:
        return await m.reply(sc("not yours"))

    sp = int(w.get("price", 100) * 0.7)

    user_col.update_one(
        {"user_id": m.from_user.id},
        {
            "$pull": {"waifus": {"mal_id": mid}},
            "$inc": {"coins": sp}
        }
    )

    await m.reply(sc(f"sold {w['name']} {sp} coins"))

@app.on_message(filters.command("daily"))
async def daily(_, m: Message):
    u = user_col.find_one({"user_id": m.from_user.id})
    now = datetime.utcnow()

    if u and u.get("last_daily"):
        if now - u["last_daily"] < timedelta(hours=24):
            return await m.reply(sc("already claimed"))

    user_col.update_one(
        {"user_id": m.from_user.id},
        {
            "$set": {"last_daily": now},
            "$inc": {"coins": 200}
        },
        upsert=True
    )

    await m.reply(sc("200 coins added"))

@app.on_message(filters.command("leaderboard"))
async def leaderboard(_, m: Message):
    users = list(user_col.find().sort("coins", -1).limit(10))

    txt = sc("top users") + "\n\n"
    for i, u in enumerate(users, 1):
        txt += f"{i}. {u.get('name','user')} — {u.get('coins',0)}\n"

    await m.reply(txt)

@app.on_inline_query()
async def inline(_, q: InlineQuery):
    query = q.query.lower()

    if not query:
        ws = list(waifu_col.aggregate([{"$sample": {"size": 5}}]))
    else:
        ws = list(waifu_col.find({"name": {"$regex": query, "$options": "i"}}).limit(5))

    res = []

    for w in ws:
        res.append(
            InlineQueryResultPhoto(
                photo_url=w["image"],
                thumb_url=w["image"],
                caption=f"{w['name']} ({w['rarity']})"
            )
        )

    await q.answer(res, cache_time=1)

app.loop.create_task(auto_drop())
