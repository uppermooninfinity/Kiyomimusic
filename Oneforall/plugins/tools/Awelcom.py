import asyncio
from logging import getLogger
from time import time

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont
from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated

from Oneforall import app
from Oneforall.utils.database import get_assistant

LOGGER = getLogger(__name__)

# -------------------- SPAM CONTROL -------------------- #
user_last_message_time = {}
user_command_count = {}

SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

# -------------------- DATABASE -------------------- #
class WelDatabase:
    def __init__(self):
        self.data = {}

    async def is_enabled(self, chat_id):
        return self.data.get(chat_id, False)

    async def enable(self, chat_id):
        self.data[chat_id] = True

    async def disable(self, chat_id):
        self.data[chat_id] = False


wlcm = WelDatabase()

# -------------------- IMAGE UTILS -------------------- #
def circle(pfp, size=(500, 500), brightness_factor=1.3):
    pfp = pfp.resize(size).convert("RGBA")
    pfp = ImageEnhance.Brightness(pfp).enhance(brightness_factor)

    mask = Image.new("L", pfp.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + pfp.size, fill=255)

    pfp.putalpha(mask)
    return pfp


def welcomepic(pic, user_id):
    background = Image.open("Oneforall/assets/wel2.png").convert("RGBA")
    pfp = Image.open(pic).convert("RGBA")

    pfp = circle(pfp)
    pfp = pfp.resize((825, 824))

    background.paste(pfp, (1990, 435), pfp)

    output = f"downloads/welcome_{user_id}.png"
    background.save(output)

    return output


# -------------------- COMMAND -------------------- #
@app.on_message(filters.command("awelcome") & ~filters.private)
async def auto_state(_, message):
    user_id = message.from_user.id
    current_time = time()

    last_time = user_last_message_time.get(user_id, 0)

    if current_time - last_time < SPAM_WINDOW_SECONDS:
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1

        if user_command_count[user_id] > SPAM_THRESHOLD:
            msg = await message.reply_text(
                f"{message.from_user.mention} Don't spam. Try again after 5 sec."
            )
            await asyncio.sleep(3)
            await msg.delete()
            return
    else:
        user_command_count[user_id] = 1

    user_last_message_time[user_id] = current_time

    # -------------------- USAGE -------------------- #
    if len(message.command) == 1:
        return await message.reply_text("Usage: /awelcome on | off")

    # -------------------- ADMIN CHECK -------------------- #
    member = await app.get_chat_member(message.chat.id, user_id)

    if member.status not in (
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    ):
        return await message.reply_text("Only admins can use this.")

    state = message.command[1].lower()
    chat_id = message.chat.id

    if state == "on":
        await wlcm.enable(chat_id)
        await message.reply_text("✅ Welcome enabled.")

    elif state == "off":
        await wlcm.disable(chat_id)
        await message.reply_text("❌ Welcome disabled.")

    else:
        await message.reply_text("Usage: /awelcome on | off")


# -------------------- WELCOME HANDLER -------------------- #
@app.on_chat_member_updated(filters.group, group=-2)
async def greet_new_members(_, member: ChatMemberUpdated):
    try:
        chat_id = member.chat.id

        # Check if enabled
        if not await wlcm.is_enabled(chat_id):
            return

        # Detect JOIN event properly
        if (
            member.old_chat_member
            and member.new_chat_member
            and member.old_chat_member.status in ("left", "kicked")
            and member.new_chat_member.status == "member"
        ):
            user = member.new_chat_member.user

            # Skip bots
            if user.is_bot:
                return

            userbot = await get_assistant(chat_id)

            username = f"@{user.username}" if user.username else "No Username"

            text = f"""
<blockquote>Welcome {user.mention}**
{username}</blockquote>
"""

            await asyncio.sleep(2)
            await userbot.send_message(chat_id, text=text)

    except Exception as e:
        LOGGER.error(f"Welcome Error: {e}")
