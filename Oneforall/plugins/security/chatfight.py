import random
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

from Oneforall import app
from config import MONGO_DB_URI, OWNER_ID
from Oneforall.misc import SUDOERS

mongo = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo["guessgame"]

users_db = db["users"]
stats_db = db["stats"]

STORAGE_CHANNEL = -1003795390770

ROUND_INTERVAL = 900  # 15 min

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

def make_gradient():
    img = Image.new("RGB", (600,300), "#1e1e2f")
    draw = ImageDraw.Draw(img)
    for i in range(300):
        color = (30+i//3, 30+i//4, 80+i//2)
        draw.line((0,i,600,i), fill=color)
    return img

def mask_word(word):
    reveal = max(1, len(word)//3)
    idx = random.sample(range(len(word)), reveal)
    return " ".join([c if i in idx else "_" for i, c in enumerate(word)])

def draw_word(word):
    img = make_gradient()
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    draw.text((80,120), mask_word(word), fill="white", font=font)

    path = f"/tmp/{word}.png"
    img.save(path)
    return path

# ---------------- GAME LOOP ---------------- #

async def send_round(client, chat_id):
    word = await get_storage_word(client)
    if not word:
        word = await get_api_word()

    ACTIVE[chat_id] = word

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
    chat_id = message.chat.id

    if chat_id in RUNNING_CHATS:
        return

    RUNNING_CHATS.add(chat_id)
    asyncio.create_task(game_loop(client, chat_id))

# ---------------- ANSWER ---------------- #

@app.on_message(filters.text & filters.group, group=2)
async def answer(client, message: Message):

    chat_id = message.chat.id

    if chat_id not in ACTIVE:
        return

    word = ACTIVE[chat_id]

    if message.text.lower() == word.lower():
        ACTIVE.pop(chat_id)

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

# ---------------- MESSAGE TRACKING ---------------- #

@app.on_message(filters.group, group=3)
async def track(client, message: Message):

    if not message.from_user:
        return

    uid = message.from_user.id
    cid = message.chat.id

    await stats_db.update_one(
        {"user_id": uid},
        {
            "$inc": {
                "global": 1,
                f"groups.{cid}.count": 1
            },
            "$set": {"name": message.from_user.first_name}
        },
        upsert=True
    )

# ---------------- PROFILE ---------------- #

@app.on_message(filters.command("profile") & filters.group)
async def profile(client, message: Message):

    uid = message.from_user.id
    cid = message.chat.id

    user = await stats_db.find_one({"user_id": uid})

    if not user:
        return await message.reply("📭 ɴᴏ ᴅᴀᴛᴀ")

    global_count = user.get("global", 0)
    group_count = user.get("groups", {}).get(str(cid), {}).get("count", 0)

    global_rank = await stats_db.count_documents({"global": {"$gt": global_count}}) + 1
    group_rank = await stats_db.count_documents({f"groups.{cid}.count": {"$gt": group_count}}) + 1

    total_users = await stats_db.count_documents({})
    total_group = await stats_db.count_documents({f"groups.{cid}": {"$exists": True}})

    if global_count < 100:
        league = "🥉 ʙʀᴏɴᴢᴇ"
        next_req = 100 - global_count
    elif global_count < 500:
        league = "🥈 sɪʟᴠᴇʀ"
        next_req = 500 - global_count
    elif global_count < 1000:
        league = "🥇 ɢᴏʟᴅ"
        next_req = 1000 - global_count
    else:
        league = "💎 ᴘʟᴀᴛɪɴᴜᴍ"
        next_req = 0

    await message.reply(
        f"👤 ʏᴏᴜʀ ᴘʀᴏғɪʟᴇ\n\n"
        f"• ʜᴇʀᴇ: {group_count}\n"
        f"• ɢʟᴏʙᴀʟ: {global_count}\n\n"
        f"• ʀᴀɴᴋ: {group_rank}/{total_group}\n"
        f"• ɢʟᴏʙᴀʟ: {global_rank}/{total_users}\n\n"
        f"{league}\n"
        f"— {next_req} ᴛᴏ ɴᴇxᴛ"
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

    await message.reply(f"✅ ɪᴍᴘᴏʀᴛᴇᴅ `{word}`")
