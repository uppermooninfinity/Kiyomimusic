import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ChatAction
from datetime import datetime, timedelta

# Import your app instance and config
try:
    from Oneforall import app
    from config import OWNER_ID, SUDOERS
except ImportError as e:
    raise ImportError(f"Could not import required modules: {e}")

class AntiBanAllManager:
    def __init__(self):
        # Track enabled chats: { chat_id: bool }
        self.enabled_chats = {}
        
        # Track locked chats: { chat_id: lock_time }
        self.locked_chats = {}
        
        # Lock duration in seconds
        self.LOCK_DURATION = 600  # 10 minutes

    def is_enabled(self, chat_id: int) -> bool:
        """Check if anti-banall is enabled for a chat."""
        return self.enabled_chats.get(chat_id, False)

    def toggle_status(self, chat_id: int, enable: bool):
        """Toggle anti-banall status for a chat."""
        self.enabled_chats[chat_id] = enable
        if not enable:
            # Clear locked chats if disabled
            self.locked_chats.pop(chat_id, None)

    def is_locked(self, chat_id: int) -> bool:
        """Check if a chat is currently locked."""
        if chat_id not in self.locked_chats:
            return False
        
        # Check if lock has expired
        lock_time = self.locked_chats[chat_id]
        if datetime.now() - lock_time > timedelta(seconds=self.LOCK_DURATION):
            del self.locked_chats[chat_id]
            return False
        
        return True

    def lock_chat(self, chat_id: int):
        """Lock a chat."""
        self.locked_chats[chat_id] = datetime.now()

    def unlock_chat(self, chat_id: int):
        """Unlock a chat."""
        if chat_id in self.locked_chats:
            del self.locked_chats[chat_id]

    async def execute_lockdown(self, client: Client, chat_id: int, attacker_id: int):
        """
        Emergency Lockdown Protocol (triggered by admin using /banall):
        1. Demote all admins (except bot itself).
        2. Lock chat permissions (no messages, no media).
        3. Kick the attacker.
        4. Lock chat for 10 minutes.
        """
        try:
            print(f"[AntiBanAll] LOCKDOWN TRIGGERED in Chat {chat_id} by Admin {attacker_id}")
            
            # Send Alert
            await client.send_message(
                chat_id,
                "🚨 **EMERGENCY LOCKDOWN ACTIVATED** 🚨\n\n"
                "Mass ban activity detected by an admin. To protect the group:\n"
                "1. All Admins have been demoted.\n"
                "2. Chat has been locked.\n"
                "3. Attacker has been removed.\n\n"
                "Chat will be unlocked in 10 minutes or use /freechat (owner only) or /revokeantibanall (OWNER_ID only)."
            )

            # Get all administrators
            admins = await client.get_chat_members(chat_id, filter="administrators")
            bot_id = (await client.get_me()).id
            
            # Demote all admins except bot
            for admin in admins:
                user_id = admin.user.id
                if user_id == bot_id:
                    continue
                
                try:
                    await client.promote_chat_member(
                        chat_id=chat_id,
                        user_id=user_id,
                        privileges=None
                    )
                    print(f"[AntiBanAll] Demoted admin: {user_id}")
                except Exception as e:
                    print(f"[AntiBanAll] Failed to demote {user_id}: {e}")

            # Lock chat permissions
            try:
                await client.set_chat_permissions(
                    chat_id=chat_id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False
                    )
                )
                print(f"[AntiBanAll] Chat {chat_id} locked.")
            except Exception as e:
                print(f"[AntiBanAll] Failed to lock chat: {e}")

            # Kick the attacker
            try:
                await client.ban_chat_member(chat_id, attacker_id)
                print(f"[AntiBanAll] Banned attacker: {attacker_id}")
            except Exception as e:
                print(f"[AntiBanAll] Failed to ban attacker: {e}")

            # Lock the chat for 10 minutes
            self.lock_chat(chat_id)

            # Schedule unlock after 10 minutes
            asyncio.create_task(self._auto_unlock(client, chat_id))

        except Exception as e:
            print(f"[AntiBanAll] Critical Error during lockdown: {e}")

    async def _auto_unlock(self, client: Client, chat_id: int):
        """Automatically unlock chat after 10 minutes."""
        await asyncio.sleep(self.LOCK_DURATION)
        
        try:
            await client.set_chat_permissions(
                chat_id=chat_id,
                permissions=ChatPermissions()  # Reset to default permissions
            )
            self.unlock_chat(chat_id)
            await client.send_message(
                chat_id,
                "✅ **LOCKDOWN LIFTED** ✅\n\nChat has been automatically unlocked after 10 minutes."
            )
            print(f"[AntiBanAll] Chat {chat_id} auto-unlocked.")
        except Exception as e:
            print(f"[AntiBanAll] Failed to auto-unlock chat {chat_id}: {e}")

    async def manual_unlock(self, client: Client, chat_id: int):
        """Manually unlock a chat."""
        try:
            await client.set_chat_permissions(
                chat_id=chat_id,
                permissions=ChatPermissions()  # Reset to default permissions
            )
            self.unlock_chat(chat_id)
            await client.send_message(
                chat_id,
                "✅ **LOCKDOWN LIFTED** ✅\n\nChat has been manually unlocked by authorized user."
            )
            print(f"[AntiBanAll] Chat {chat_id} manually unlocked.")
        except Exception as e:
            print(f"[AntiBanAll] Failed to unlock chat {chat_id}: {e}")

# Instantiate Manager
anti_ban_mgr = AntiBanAllManager()

# --- HANDLERS ---

@app.on_message(filters.command("antibanall") & filters.group)
async def handle_antibanall_command(client, message):
    """
    Command: /antibanall
    Shows status and toggle buttons.
    Only chat admins, OWNER_ID, or SUDOERS can use this.
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if user is authorized
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        await message.reply_text(f"❌ Error checking user status: {e}")
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only chat admins, OWNER_ID, or SUDOERS can use this command.")
        return
    
    # Get current status
    is_enabled = anti_ban_mgr.is_enabled(chat_id)
    status_text = "✅ **ENABLED**" if is_enabled else "❌ **DISABLED**"
    
    # Create inline buttons
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Enable" if not is_enabled else "☑️ Enabled",
                    callback_data=f"antibanall_enable_{chat_id}"
                ),
                InlineKeyboardButton(
                    "❌ Disable" if is_enabled else "☐ Disabled",
                    callback_data=f"antibanall_disable_{chat_id}"
                )
            ]
        ]
    )
    
    response_text = (
        "🛡️ **Anti-BanAll System**\n\n"
        f"**Current Status:** {status_text}\n\n"
        "This system protects your group from mass ban attacks:\n"
        "• Normal members attempting /banall are kicked\n"
        "• Admins attempting /banall trigger lockdown\n"
        "• Chat is locked for 10 minutes\n"
        "• All admins are demoted\n\n"
        "Use the buttons below to toggle the system."
    )
    
    await message.reply_text(response_text, reply_markup=keyboard)
    print(f"[AntiBanAll] /antibanall command used by {user_id} in chat {chat_id}")

@app.on_callback_query()
async def handle_antibanall_callback(client, callback_query):
    """Handle inline button callbacks for antibanall toggle."""
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    # Check if this is an antibanall callback
    if not data.startswith("antibanall_"):
        return
    
    chat_id = int(data.split("_")[-1])
    action = data.split("_")[1]
    
    # Check if user is authorized
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        await callback_query.answer(f"❌ Error: {e}", show_alert=True)
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    
    if not (is_admin or is_owner_or_sudo):
        await callback_query.answer("❌ You are not authorized to use this.", show_alert=True)
        return
    
    # Handle enable/disable
    if action == "enable":
        anti_ban_mgr.toggle_status(chat_id, True)
        await callback_query.answer("✅ Anti-BanAll System Enabled!", show_alert=False)
        print(f"[AntiBanAll] Anti-BanAll enabled in chat {chat_id} by {user_id}")
        
        # Update message
        is_enabled = anti_ban_mgr.is_enabled(chat_id)
        status_text = "✅ **ENABLED**" if is_enabled else "❌ **DISABLED**"
        
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Enable" if not is_enabled else "☑️ Enabled",
                        callback_data=f"antibanall_enable_{chat_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Disable" if is_enabled else "☐ Disabled",
                        callback_data=f"antibanall_disable_{chat_id}"
                    )
                ]
            ]
        )
        
        response_text = (
            "🛡️ **Anti-BanAll System**\n\n"
            f"**Current Status:** {status_text}\n\n"
            "This system protects your group from mass ban attacks:\n"
            "• Normal members attempting /banall are kicked\n"
            "• Admins attempting /banall trigger lockdown\n"
            "• Chat is locked for 10 minutes\n"
            "• All admins are demoted\n\n"
            "Use the buttons below to toggle the system."
        )
        
        await callback_query.edit_message_text(response_text, reply_markup=keyboard)
        
    elif action == "disable":
        anti_ban_mgr.toggle_status(chat_id, False)
        await callback_query.answer("❌ Anti-BanAll System Disabled!", show_alert=False)
        print(f"[AntiBanAll] Anti-BanAll disabled in chat {chat_id} by {user_id}")
        
        # Update message
        is_enabled = anti_ban_mgr.is_enabled(chat_id)
        status_text = "✅ **ENABLED**" if is_enabled else "❌ **DISABLED**"
        
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Enable" if not is_enabled else "☑️ Enabled",
                        callback_data=f"antibanall_enable_{chat_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Disable" if is_enabled else "☐ Disabled",
                        callback_data=f"antibanall_disable_{chat_id}"
                    )
                ]
            ]
        )
        
        response_text = (
            "🛡️ **Anti-BanAll System**\n\n"
            f"**Current Status:** {status_text}\n\n"
            "This system protects your group from mass ban attacks:\n"
            "• Normal members attempting /banall are kicked\n"
            "• Admins attempting /banall trigger lockdown\n"
            "• Chat is locked for 10 minutes\n"
            "• All admins are demoted\n\n"
            "Use the buttons below to toggle the system."
        )
        
        await callback_query.edit_message_text(response_text, reply_markup=keyboard)

@app.on_message(filters.command("banall") & filters.group)
async def handle_banall_command(client, message):
    """
    Command: /banall
    - If anti-banall is disabled, ignore
    - If normal member uses it: kick the member
    - If admin uses it: demote all admins, lock chat for 10 minutes, and kick the admin
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if anti-banall is enabled
    if not anti_ban_mgr.is_enabled(chat_id):
        return
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        user_status = member.status
    except Exception as e:
        await message.reply_text(f"❌ Error checking user status: {e}")
        return

    if user_status == ChatMemberStatus.OWNER:
        # Chat owner using /banall - kick them too
        await message.reply_text("⚠️ Even the chat owner cannot use /banall!")
        try:
            await client.ban_chat_member(chat_id, user_id)
            print(f"[AntiBanAll] Kicked chat owner {user_id} for using /banall")
        except Exception as e:
            print(f"[AntiBanAll] Failed to kick owner: {e}")
        return

    if user_status == ChatMemberStatus.ADMINISTRATOR:
        # Admin trying to ban everyone - execute lockdown
        await anti_ban_mgr.execute_lockdown(client, chat_id, user_id)
        return

    # Normal member trying to use /banall - kick them
    try:
        await client.ban_chat_member(chat_id, user_id)
        await message.reply_text(f"❌ User {message.from_user.mention} has been kicked for attempting to ban everyone!")
        print(f"[AntiBanAll] Kicked normal member {user_id} for using /banall")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
        print(f"[AntiBanAll] Failed to kick member {user_id}: {e}")

@app.on_message(filters.command("freechat") & filters.group)
async def handle_freechat_command(client, message):
    """
    Command: /freechat
    Only chat owner can use this to unlock the chat.
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status != ChatMemberStatus.OWNER:
            await message.reply_text("❌ Only the chat owner can use this command.")
            return
        
        if not anti_ban_mgr.is_locked(chat_id):
            await message.reply_text("❌ Chat is not currently locked.")
            return
        
        await anti_ban_mgr.manual_unlock(client, chat_id)
        print(f"[AntiBanAll] Chat {chat_id} unlocked by owner {user_id}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
        print(f"[AntiBanAll] Error in /freechat: {e}")

@app.on_message(filters.command("revokeantibanall") & filters.private)
async def handle_revokeantibanall_command(client, message):
    """
    Command: /revokeantibanall <chat_id>
    Only OWNER_ID (from config) or SUDOERS can use this to unlock any chat.
    """
    user_id = message.from_user.id
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    
    if not is_owner_or_sudo:
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: `/revokeantibanall <chat_id>`")
        return
    
    try:
        chat_id = int(args[1])
    except ValueError:
        await message.reply_text("❌ Invalid chat ID. Please provide a valid integer.")
        return
    
    try:
        if not anti_ban_mgr.is_locked(chat_id):
            await message.reply_text(f"❌ Chat {chat_id} is not currently locked.")
            return
        
        await anti_ban_mgr.manual_unlock(client, chat_id)
        await message.reply_text(f"✅ Chat {chat_id} has been unlocked.")
        print(f"[AntiBanAll] Chat {chat_id} unlocked by OWNER_ID/SUDOER {user_id}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
        print(f"[AntiBanAll] Error in /revokeantibanall: {e}")
