
import asyncio
from datetime import datetime
from typing import Optional, Dict, Tuple

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, MessageEntityType
from pyrogram.errors import PeerIdInvalid, UserNotParticipant

from Oneforall import app
from Oneforall.core.mongo import mongodb
from Oneforall.misc import SUDOERS
from Oneforall.utils.functions import (
    extract_user,
    extract_text_and_keyb,
    check_format,
    get_file_id_from_message,
)
from Oneforall.utils.permissions import adminsOnly, member_permissions
from config import OWNER_ID

__MODULE__ = "ꜱᴇᴄᴜʀɪᴛʏ"
__HELP__ = """
/setwelcome - ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɪᴍᴀɢᴇ ᴡɪᴛʜ ᴄᴀᴘᴛɪᴏɴ
/delwelcome - ᴅᴇʟᴇᴛᴇ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ
/getwelcome - ɢᴇᴛ ᴄᴜʀʀᴇɴᴛ ᴡᴇʟᴄᴏᴍᴇ
"""

# Initialize database collections
welc_db = mongodb.welcome
welc_settings_db = mongodb.welcome_settings

# Supported variable fillings
SUPPORTED_VARIABLES = {
    "{GROUPNAME}": "Group's name",
    "{NAME}": "User name (first + last)",
    "{ID}": "User ID",
    "{FIRSTNAME}": "User first name",
    "{SURNAME}": "User surname (if exists)",
    "{USERNAME}": "User username",
    "{TIME}": "Today's time",
    "{DATE}": "Today's date",
    "{WEEKDAY}": "Today's weekday",
}

MARKDOWN_HELP = """
<u>ꜱᴜᴘᴘᴏʀᴛᴇᴅ ғᴏʀᴍᴀᴛᴛɪɴɢ:</u>

<code>**Bold**</code> : ᴛʜɪs ᴡɪʟʟ sʜᴏᴡ ᴀs <b>Bold</b> ᴛᴇxᴛ.
<code>~~strike~~</code>: ᴛʜɪs ᴡɪʟʟ sʜᴏᴡ ᴀs <strike>strike</strike> ᴛᴇxᴛ.
<code>__italic__</code>: ᴛʜɪs ᴡɪʟʟ sʜᴏᴡ ᴀs <i>italic</i> ᴛᴇxᴛ
<code>--underline--</code>: ᴛʜɪs ᴡɪʟʟ sʜᴏᴡ ᴀs <u>underline</u> ᴛᴇxᴛ.
<code>`code words`</code>: ᴛʜɪs ᴡɪʟʟ sʜᴏᴡ ᴀs <code>code</code> ᴛᴇxᴛ.
<code>||spoiler||</code>: ᴛʜɪs ᴡɪʟʟ sʜᴏᴡ ᴀs <spoiler>Spoiler</spoiler> ᴛᴇxᴛ.
<code>[hyperlink](google.com)</code>: ᴛʜɪs ᴡɪʟʟ ᴄʀᴇᴀᴛᴇ ᴀ <a href='https://www.google.com'>hyperlink</a> text
<code>> hello</code> ᴛʜɪs ᴡɪʟʟ sʜᴏᴡ ᴀs <blockquote>hello</blockquote>

<b>ᴀᴅᴅ ʙᴜᴛᴛᴏɴs ᴜsɪɴɢ:</b>
text ~ [button text, button link]
"""

# ==================== HELPER FUNCTIONS ====================


async def get_welcome_data(chat_id: int) -> Optional[Dict]:
    """Retrieve welcome message data from database"""
    try:
        data = await welc_db.find_one({"chat_id": chat_id})
        return data
    except Exception as e:
        print(f"Error fetching welcome data: {e}")
        return None


async def save_welcome_data(
    chat_id: int,
    text: str,
    file_id: Optional[str] = None,
    media_type: Optional[str] = None,
    keyboard: Optional[Dict] = None,
) -> bool:
    """Save welcome message data to database"""
    try:
        data = {
            "chat_id": chat_id,
            "text": text,
            "file_id": file_id,
            "media_type": media_type,
            "keyboard": keyboard,
            "created_at": datetime.now(),
        }
        await welc_db.update_one(
            {"chat_id": chat_id}, {"$set": data}, upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving welcome data: {e}")
        return False


async def delete_welcome_data(chat_id: int) -> bool:
    """Delete welcome message data from database"""
    try:
        await welc_db.delete_one({"chat_id": chat_id})
        return True
    except Exception as e:
        print(f"Error deleting welcome data: {e}")
        return False


async def format_welcome_text(
    text: str, user_id: int, chat_id: int, client: Client
) -> str:
    """Format welcome text with user and group variables"""
    try:
        user = await client.get_users(user_id)
        chat = await client.get_chat(chat_id)

        # Get current date/time
        now = datetime.now()
        weekday = ["ᴍᴏɴᴅᴀʏ", "ᴛᴜᴇsᴅᴀʏ", "ᴡᴇᴅɴᴇsᴅᴀʏ", "ᴛʜᴜʀsᴅᴀʏ", "ғʀɪᴅᴀʏ", "sᴀᴛᴜʀᴅᴀʏ", "sᴜɴᴅᴀʏ"]

        # Replace variables
        formatted_text = text.replace("{GROUPNAME}", chat.title or "Group")
        formatted_text = formatted_text.replace("{NAME}", user.first_name or "")
        if user.last_name:
            formatted_text = formatted_text.replace(
                "{NAME}", f"{user.first_name} {user.last_name}"
            )
        formatted_text = formatted_text.replace("{ID}", str(user_id))
        formatted_text = formatted_text.replace("{FIRSTNAME}", user.first_name or "")
        formatted_text = formatted_text.replace(
            "{SURNAME}", user.last_name or ""
        )
        formatted_text = formatted_text.replace(
            "{USERNAME}", f"@{user.username}" if user.username else "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ"
        )
        formatted_text = formatted_text.replace(
            "{TIME}", now.strftime("%H:%M:%S")
        )
        formatted_text = formatted_text.replace(
            "{DATE}", now.strftime("%d/%m/%Y")
        )
        formatted_text = formatted_text.replace(
            "{WEEKDAY}", weekday[now.weekday()]
        )

        return formatted_text
    except Exception as e:
        print(f"Error formatting welcome text: {e}")
        return text


# ==================== COMMANDS ====================


@app.on_message(
    filters.command("setwelcome")
    & filters.group
    & ~filters.edited
)
@adminsOnly
async def set_welcome(client: Client, message: Message):
    """Set welcome message with optional image attachment"""
    try:
        chat_id = message.chat.id
        
        # Check if it's a reply
        if not message.reply_to_message:
            await message.reply_text(
                "ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɪᴍᴀɢᴇ ᴛᴏ sᴇᴛ ɪᴛ ᴀs ᴡᴇʟᴄᴏᴍᴇ.\n\n"
                f"<b>sᴜᴘᴘᴏʀᴛᴇᴅ ᴠᴀʀɪᴀʙʟᴇs:</b>\n"
                + "\n".join([f"<code>{k}</code> - {v}" for k, v in SUPPORTED_VARIABLES.items()]),
                parse_mode="html"
            )
            return

        replied_msg = message.reply_to_message
        
        # Extract text/caption
        welcome_text = replied_msg.text or replied_msg.caption or "ᴡᴇʟᴄᴏᴍᴇ {NAME}!"
        
        # Check format and extract keyboard if present
        keyboard_data = None
        file_id = None
        media_type = None
        
        # Format checking
        welcome_text = await check_format(lambda kb, rw: kb, welcome_text)
        
        # Extract keyboard if present
        extracted = extract_text_and_keyb(
            lambda kb, rw: InlineKeyboardMarkup([[InlineKeyboardButton(k, url=v) for k, v in kb.items()]]),
            welcome_text
        )
        
        if extracted:
            welcome_text, keyboard_data = extracted
        
        # Handle media (photo, video, animation, sticker, document)
        if replied_msg.photo:
            media_type = "photo"
            file_id = replied_msg.photo.file_id
        elif replied_msg.video:
            media_type = "video"
            file_id = replied_msg.video.file_id
        elif replied_msg.animation:
            media_type = "animation"
            file_id = replied_msg.animation.file_id
        elif replied_msg.sticker:
            media_type = "sticker"
            file_id = replied_msg.sticker.file_id
        elif replied_msg.document:
            media_type = "document"
            file_id = replied_msg.document.file_id
        
        # Save to database
        success = await save_welcome_data(
            chat_id=chat_id,
            text=welcome_text,
            file_id=file_id,
            media_type=media_type,
            keyboard=keyboard_data,
        )
        
        if success:
            msg_type = "ᴍᴇssᴀɢᴇ" if not media_type else f"{media_type} ᴍᴇssᴀɢᴇ"
            await message.reply_text(
                f"✅ ᴡᴇʟᴄᴏᴍᴇ {msg_type} sᴇᴛ sᴜᴄᴄᴇsꜱғᴜʟʟʏ!",
                quote=True
            )
        else:
            await message.reply_text(
                "❌ ᴇʀʀᴏʀ sᴀᴠɪɴɢ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ",
                quote=True
            )
    except Exception as e:
        await message.reply_text(
            f"❌ ᴇʀʀᴏʀ: {str(e)[:100]}",
            quote=True
        )


@app.on_message(
    filters.command("getwelcome")
    & filters.group
    & ~filters.edited
)
async def get_welcome(client: Client, message: Message):
    """Get current welcome message"""
    try:
        chat_id = message.chat.id
        welcome_data = await get_welcome_data(chat_id)
        
        if not welcome_data:
            await message.reply_text(
                "ɴᴏ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ sᴇᴛ. ᴜsᴇ /setwelcome ᴛᴏ sᴇᴛ ᴏɴᴇ.",
                quote=True
            )
            return
        
        welcome_text = welcome_data.get("text", "")
        media_type = welcome_data.get("media_type")
        file_id = welcome_data.get("file_id")
        keyboard = welcome_data.get("keyboard")
        
        # Create keyboard markup if exists
        inline_kb = None
        if keyboard:
            buttons = []
            for i, (text, url) in enumerate(keyboard.items()):
                buttons.append(InlineKeyboardButton(text, url=url))
            inline_kb = InlineKeyboardMarkup([buttons])
        
        # Send welcome message preview
        if media_type and file_id:
            if media_type == "photo":
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=file_id,
                    caption=welcome_text,
                    reply_markup=inline_kb,
                    quote=True
                )
            elif media_type == "video":
                await client.send_video(
                    chat_id=message.chat.id,
                    video=file_id,
                    caption=welcome_text,
                    reply_markup=inline_kb,
                    quote=True
                )
            elif media_type == "animation":
                await client.send_animation(
                    chat_id=message.chat.id,
                    animation=file_id,
                    caption=welcome_text,
                    reply_markup=inline_kb,
                    quote=True
                )
            elif media_type == "sticker":
                await client.send_sticker(
                    chat_id=message.chat.id,
                    sticker=file_id,
                    quote=True
                )
                if welcome_text:
                    await message.reply_text(welcome_text, reply_markup=inline_kb)
            elif media_type == "document":
                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_id,
                    caption=welcome_text,
                    reply_markup=inline_kb,
                    quote=True
                )
        else:
            await message.reply_text(
                welcome_text,
                reply_markup=inline_kb,
                quote=True
            )
    except Exception as e:
        await message.reply_text(
            f"❌ ᴇʀʀᴏʀ: {str(e)[:100]}",
            quote=True
        )


@app.on_message(
    filters.command("delwelcome")
    & filters.group
    & ~filters.edited
)
@adminsOnly
async def del_welcome(client: Client, message: Message):
    """Delete welcome message"""
    try:
        chat_id = message.chat.id
        success = await delete_welcome_data(chat_id)
        
        if success:
            await message.reply_text(
                "✅ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ ᴅᴇʟᴇᴛᴇᴅ!",
                quote=True
            )
        else:
            await message.reply_text(
                "❌ ɴᴏ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ ғᴏᴜɴᴅ",
                quote=True
            )
    except Exception as e:
        await message.reply_text(
            f"❌ ᴇʀʀᴏʀ: {str(e)[:100]}",
            quote=True
        )


@app.on_message(filters.new_chat_members & filters.group)
async def welcome_members(client: Client, message: Message):
    """Send welcome message to new members"""
    try:
        chat_id = message.chat.id
        welcome_data = await get_welcome_data(chat_id)
        
        if not welcome_data:
            return
        
        for member in message.new_chat_members:
            if member.is_self:
                continue
            
            try:
                # Format welcome text with user data
                welcome_text = await format_welcome_text(
                    welcome_data.get("text", "ᴡᴇʟᴄᴏᴍᴇ {NAME}!"),
                    member.id,
                    chat_id,
                    client
                )
                
                media_type = welcome_data.get("media_type")
                file_id = welcome_data.get("file_id")
                keyboard = welcome_data.get("keyboard")
                
                # Create keyboard markup if exists
                inline_kb = None
                if keyboard:
                    buttons = []
                    for text, url in keyboard.items():
                        buttons.append(InlineKeyboardButton(text, url=url))
                    inline_kb = InlineKeyboardMarkup([buttons])
                
                # Send welcome message with media
                if media_type and file_id:
                    if media_type == "photo":
                        await client.send_photo(
                            chat_id=chat_id,
                            photo=file_id,
                            caption=welcome_text,
                            reply_markup=inline_kb
                        )
                    elif media_type == "video":
                        await client.send_video(
                            chat_id=chat_id,
                            video=file_id,
                            caption=welcome_text,
                            reply_markup=inline_kb
                        )
                    elif media_type == "animation":
                        await client.send_animation(
                            chat_id=chat_id,
                            animation=file_id,
                            caption=welcome_text,
                            reply_markup=inline_kb
                        )
                    elif media_type == "sticker":
                        await client.send_sticker(
                            chat_id=chat_id,
                            sticker=file_id
                        )
                        if welcome_text:
                            await client.send_message(
                                chat_id=chat_id,
                                text=welcome_text,
                                reply_markup=inline_kb
                            )
                    elif media_type == "document":
                        await client.send_document(
                            chat_id=chat_id,
                            document=file_id,
                            caption=welcome_text,
                            reply_markup=inline_kb
                        )
                else:
                    await client.send_message(
                        chat_id=chat_id,
                        text=welcome_text,
                        reply_markup=inline_kb
                    )
                
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Error sending welcome to user {member.id}: {e}")
                continue
    except Exception as e:
        print(f"Error in welcome_members: {e}")
