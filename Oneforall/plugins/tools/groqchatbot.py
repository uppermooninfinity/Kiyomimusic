from Oneforall import app
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatMemberStatus
from groq import Groq
from os import getenv

# ─── CONFIG ──────────────────────────────────────────
BOT_USERNAME = getenv("BOT_USERNAME", "Snowy music").lower()
groq = Groq(api_key=getenv("GROQ_API_KEY"))

BLOCKED_COMMANDS = (
    "/play", "/vplay", "/cplay", "/seek", "/seekback",
    "/pause", "/resume", "/skip", "/end", "/stop",
    "/afk", "/ping", "/start", "/help"
)

SYSTEM_PROMPT = """
Your name is Snowy.
You are a human-like bestfriend.
You talk casually with emotions and emojis 😄✨
You are funny, caring, sometimes playful.
Never say you are an AI.
Keep replies short, natural and friendly.
No images, text only.
"""

# ─── MEMORY ──────────────────────────────────────────
USER_MEMORY = {}

def add_memory(uid, role, text):
    USER_MEMORY.setdefault(uid, []).append(
        {"role": role, "content": text}
    )
    USER_MEMORY[uid] = USER_MEMORY[uid][-6:]

# ─── CHATBOT TOGGLE STORAGE ──────────────────────────
CHATBOT_STATUS = {}

# ─── ADMIN CHECK ─────────────────────────────────────
async def is_admin(client, message):
    try:
        member = await client.get_chat_member(
            message.chat.id, message.from_user.id
        )
        return member.status in [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        ]
    except:
        return False

# ─── TOGGLE COMMAND ──────────────────────────────────
@app.on_message(filters.command(["chatbot", "talk"]) & filters.group)
async def toggle_chatbot(client, message):
    if not await is_admin(client, message):
        return await message.reply_text("❌ Only admins can use this.")

    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:**\n/chatbot on\n/chatbot off"
        )

    action = message.command[1].lower()

    if action == "on":
        CHATBOT_STATUS[message.chat.id] = True
        await message.reply_text("✅ Chatbot enabled 🤖")
    elif action == "off":
        CHATBOT_STATUS[message.chat.id] = False
        await message.reply_text("❌ Chatbot disabled")
    else:
        await message.reply_text("Use 'on' or 'off'")

# ─── CHAT HANDLER ────────────────────────────────────
@app.on_message(filters.text & ~filters.command)
async def shivani_chat(bot, message):
    if not message.from_user:
        return

    # ❗ CHECK TOGGLE (only for groups)
    if message.chat.type != "private":
        if not CHATBOT_STATUS.get(message.chat.id, False):
            return

    text = message.text.strip()

    # Ignore music/system commands
    if text.startswith(BLOCKED_COMMANDS):
        return

    # ─── TRIGGER LOGIC ───
    if message.chat.type == "private":
        triggered = True
    else:
        mentioned = f"@{BOT_USERNAME}" in text.lower()
        replied = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.is_bot
        )
        triggered = mentioned or replied

    if not triggered:
        return

    # Clean mention
    clean_text = text.replace(f"@{BOT_USERNAME}", "").strip()
    user_id = message.from_user.id

    add_memory(user_id, "user", clean_text)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(USER_MEMORY[user_id])

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.9,
            max_tokens=200
        )

        reply = response.choices[0].message.content.strip()
        add_memory(user_id, "assistant", reply)

        await message.reply_text(reply)

    except Exception:
        await message.reply_text("😅 Oops… thoda lag ho gaya, phir bolo na!")
