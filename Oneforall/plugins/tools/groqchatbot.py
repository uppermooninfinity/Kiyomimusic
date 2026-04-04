import os
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Oneforall import app
from groq import Groq

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Store chatbot status per chat
CHATBOT_STATUS = {}

# Helper to remove mentions
def clean_text(message: Message) -> str:
    text = message.text or ""
    if message.entities:
        for ent in message.entities:
            if ent.type == "mention":
                text = text.replace(ent.text, "").strip()
    return text


# ─── TOGGLE COMMAND ─────────────────────────────────────────

@app.on_message(filters.command("chatbot") & filters.group)
async def chatbot_toggle(client, message: Message):
    chat_id = message.chat.id
    args = message.command

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Enable", callback_data="chatbot_on"),
            InlineKeyboardButton("❌ Disable", callback_data="chatbot_off"),
        ]
    ])

    # If user typed /chatbot on/off
    if len(args) > 1:
        if args[1].lower() == "on":
            CHATBOT_STATUS[chat_id] = True
            return await message.reply_text("🤖 Chatbot enabled in this chat.")
        elif args[1].lower() == "off":
            CHATBOT_STATUS[chat_id] = False
            return await message.reply_text("🤖 Chatbot disabled in this chat.")

    # Default: show buttons
    await message.reply_text(
        "⚙️ **Chatbot Settings**\nChoose an option:",
        reply_markup=keyboard
    )


# ─── CALLBACK HANDLER ──────────────────────────────────────

@app.on_callback_query(filters.regex("^chatbot_"))
async def chatbot_buttons(client, query: CallbackQuery):
    chat_id = query.message.chat.id

    if query.data == "chatbot_on":
        CHATBOT_STATUS[chat_id] = True
        await query.answer("Enabled ✅", show_alert=False)
        await query.edit_message_text("🤖 Chatbot has been enabled.")

    elif query.data == "chatbot_off":
        CHATBOT_STATUS[chat_id] = False
        await query.answer("Disabled ❌", show_alert=False)
        await query.edit_message_text("🤖 Chatbot has been disabled.")


# ─── CHATBOT HANDLER ───────────────────────────────────────

@app.on_message(filters.text & ~filters.bot & filters.group)
async def groq_chat_handler(client, message: Message):
    chat_id = message.chat.id

    # Check if chatbot is enabled
    if not CHATBOT_STATUS.get(chat_id, False):
        return

    text = clean_text(message)

    # Ignore commands
    if not text or text.startswith(("/", "!", "?", "@", "#")):
        return

    await client.send_chat_action(chat_id, ChatAction.TYPING)

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text},
        ]

        result = await asyncio.to_thread(
            groq_client.chat.completions.create,
            messages=messages,
            model="openai/gpt-oss-20b"
        )

        reply = result.choices[0].message.content

        if reply:
            await message.reply_text(reply)
        else:
            await message.reply_text("🤖 I got no answer — try again!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        await message.reply_text(f"❌ Error: {e}")
