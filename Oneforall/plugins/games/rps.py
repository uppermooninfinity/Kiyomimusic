from Oneforall import app
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import random

games = {}
leaderboards = defaultdict(lambda: defaultdict(int))

PREFIXES = ["/", ".", "!"]
OPTIONS = ["rock", "paper", "scissors"]

def sc(text):
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    result = ""
    for ch in text:
        if ch.lower() in normal:
            result += small[normal.index(ch.lower())]
        else:
            result += ch
    return result

@app.on_message(filters.command("rps", prefixes=PREFIXES) & filters.group)
async def start_rps(client, message):
    text = sc("rock paper scissors\nchoose your move")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🪨", callback_data="rps_play:rock"),
                InlineKeyboardButton("📄", callback_data="rps_play:paper"),
                InlineKeyboardButton("✂️", callback_data="rps_play:scissors")
            ]
        ]
    )
    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("^rps_play:"))
async def rps_callbacks(client, callback_query):
    chat_id = callback_query.message.chat.id
    user = callback_query.from_user
    choice = callback_query.data.split(":")[1]

    bot_choice = random.choice(OPTIONS)

    if choice == bot_choice:
        result = sc("draw")
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = sc("you win")
        leaderboards[chat_id][user.id] += 1
    else:
        result = sc("you lose")

    text = (
        f"{user.mention}\n"
        f"{sc('you')} : {choice}\n"
        f"{sc('bot')} : {bot_choice}\n\n"
        f"{result}"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("play again", callback_data="rps_again")]
        ]
    )

    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@app.on_callback_query(filters.regex("^rps_again$"))
async def rps_again(client, callback_query):
    text = sc("choose again")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🪨", callback_data="rps_play:rock"),
                InlineKeyboardButton("📄", callback_data="rps_play:paper"),
                InlineKeyboardButton("✂️", callback_data="rps_play:scissors")
            ]
        ]
    )
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()

@app.on_message(filters.command("rpslead", prefixes=PREFIXES) & filters.group)
async def leaderboard(client, message):
    chat_id = message.chat.id

    if chat_id not in leaderboards or not leaderboards[chat_id]:
        return await message.reply_text(sc("no games played"))

    sorted_users = sorted(leaderboards[chat_id].items(), key=lambda x: x[1], reverse=True)

    text = sc("leaderboard") + "\n\n"

    for i, (user_id, wins) in enumerate(sorted_users[:10], 1):
        text += f"{i}. [user](tg://user?id={user_id}) - {wins}\n"

    await message.reply_text(text, disable_web_page_preview=True)
