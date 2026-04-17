import random
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pyrogram import filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

from Oneforall import app
from config import MONGO_DB_URI, OWNER_ID
from Oneforall.misc import SUDOERS

mongo = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo["guessgame"]

users_db = db["users"]
group_db = db["groups"]

# 🔥 CHANGE THIS
STORAGE_CHANNEL = -1001234567890

ROUND_INTERVAL = 900

ACTIVE = {}
RUNNING_CHATS = set()

REACTIONS = [
    "💞","💗","👀","✅","❄️","😁","🥳","🤩","😎","💫","✨","🌟","💥",
    "❤️","🧡","💛","🩵","💙","💜","🤎","🎊","🩶","🩷","💘","💓",
    "💖","💕","💌","💟","♥️","❣️","❤️‍🩹","❤️‍🔥","🧠"
]

# ---------------- WORD SYSTEM ---------------- #

async def get_api_word():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://random-word-api.herokuapp.com/word") as r:
                return (await r.json())[0]
    except:
        return random.choice(["apple","tiger","dragon","piano"])

async def get_storage_word(client):
    try:
        words = []
        async for m in client.get_chat_history(STORAGE_CHANNEL, limit=50):
            if m.caption and m.caption.startswith("WORD:"):
                words.append(m.caption.split("WORD:")[1].strip())
        if words:
            return random.choice(words)
    except:
        pass
    return None

# ---------------- UI ---------------- #

def draw_word(word):
    base = Image.new("RGB", (600, 350), "#0f172a")

    blur = Image.new("RGB", (600, 350), "#1e293b")
    blur = blur.filter(ImageFilter.GaussianBlur(20))
    base.paste(blur, (0, 0))

    overlay = Image.new("RGBA", base.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((50, 80, 550, 280), radius=40, fill=(255,255,255,40))

    base = Image.alpha_composite(base.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(base)

    try:
        font = ImageFont.truetype("Oneforall/assets/Poppins-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()

    text = word.upper()

    bbox = draw.textbbox((0,0), text, font=font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]

    x = (600 - w)//2
    y = (350 - h)//2

    draw.text((x+3,y+3), text, fill=(0,0,0,120), font=font)
    draw.text((x,y), text, fill="white", font=font)

    path = f"/tmp/{word}.png"
    base.save(path)
    return path

# ---------------- GAME ---------------- #

async def send_round(client, chat_id):
    word = await get_storage_word(client) or await get_api_word()
    ACTIVE[chat_id] = word.lower()

    img = draw_word(word)

    try:
        await client.send_photo(
            chat_id,
            img,
            caption="🎯 ɢᴜᴇss ᴛʜᴇ ᴡᴏʀᴅ\n🧠 ᴛʏᴘᴇ ғᴀsᴛ",
            has_spoiler=True
        )
    except:
        pass

async def game_loop(client, chat_id):
    while chat_id in RUNNING_CHATS:
        await send_round(client, chat_id)
        await asyncio.sleep(ROUND_INTERVAL)

# ---------------- AUTO START ---------------- #

@app.on_message(filters.group, group=1)
async def auto_start(client, message: Message):
    cid = message.chat.id

    if cid not in RUNNING_CHATS:
        RUNNING_CHATS.add(cid)
        asyncio.create_task(game_loop(client, cid))

# ---------------- ANSWER ---------------- #

@app.on_message(filters.text & filters.group, group=2)
async def answer(client, message: Message):

    cid = message.chat.id

    if cid not in ACTIVE:
        return

    if message.text.lower() == ACTIVE[cid]:
        ACTIVE.pop(cid)

        try:
            await message.react(random.choice(REACTIONS))
        except:
            pass

        user = await users_db.find_one({"id": message.from_user.id})
        coins = user["coins"] if user else 0
        coins += 10

        await users_db.update_one(
            {"id": message.from_user.id},
            {"$set": {"coins": coins, "name": message.from_user.first_name}},
            upsert=True
        )

        await message.reply(
            f"🏆 ᴄᴏʀʀᴇᴄᴛ\n👤 {message.from_user.mention}\n💰 +10\n🪙 {coins}"
        )

# ---------------- IMPORT ---------------- #

@app.on_message(filters.command("import") & filters.group)
async def import_word(client, message: Message):

    if message.from_user.id not in SUDOERS and message.from_user.id != OWNER_ID:
        return await message.reply("🚫 ɴᴏ ᴀᴄᴄᴇss")

    if len(message.command) < 2:
        return await message.reply("⚠️ /ɪᴍᴘᴏʀᴛ ᴡᴏʀᴅ")

    word = message.command[1].lower()

    img = draw_word(word)

    await client.send_photo(
        STORAGE_CHANNEL,
        img,
        caption=f"WORD:{word}",
        has_spoiler=True
    )

    await message.reply(f"✅ ɪᴍᴘᴏʀᴛᴇᴅ {word}")

# ---------------- MILESTONE ---------------- #

@app.on_message(filters.group, group=3)
async def track_group(client, message: Message):

    cid = message.chat.id

    data = await group_db.find_one({"chat_id": cid})

    count = data.get("count", 0) + 1 if data else 1
    last = data.get("last", 0) if data else 0

    milestone = (count // 5000) * 5000

    await group_db.update_one(
        {"chat_id": cid},
        {"$set": {"count": count}},
        upsert=True
    )

    if milestone > 0 and milestone > last:
        await group_db.update_one(
            {"chat_id": cid},
            {"$set": {"last": milestone}}
        )

        await message.reply(
            f"🎉 ᴄᴏɴɢʀᴀᴛs\n💬 ɢʀᴏᴜᴘ ʀᴇᴀᴄʜᴇᴅ {milestone} ᴍᴇssᴀɢᴇs"
        )

# ---------------- LEADERBOARD ---------------- #

LEADERBOARD_VIDEO = "https://graph.org/file/5a27e77b6bcec50ff4c73-a3af79edc5d50d6273.mp4"

@app.on_message(filters.command("gametop") & filters.group)
async def gametop(client, message: Message):

    users = users_db.find().sort("coins", -1).limit(10)

    text = "🏆 ɢᴀᴍᴇ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"

    i = 1
    async for u in users:
        text += f"{i}. {u.get('name')} — {u.get('coins',0)} 🪙\n"
        i += 1

    try:
        await message.reply_video(
            LEADERBOARD_VIDEO,
            caption=text
        )
    except:
        await message.reply(text)
