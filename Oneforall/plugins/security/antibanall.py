import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus, ChatAction
from datetime import datetime, timedelta

# Import your app instance from Oneforall
try:
    from Oneforall import app
except ImportError:
    raise ImportError("Could not import 'app' from Oneforall. Ensure Oneforall is in your path.")

class AntiBanAllManager:
    def __init__(self):
        # Store enabled status per chat_id: { chat_id: bool }
        self.enabled_chats = {}
        
        # Thresholds
        self.BAN_THRESHOLD = 3  # Number of bans within time window to trigger
        self.TIME_WINDOW = 2.0  # Seconds window to count bans
        
        # Track recent bans per chat: { chat_id: [timestamp1, timestamp2, ...] }
        self.recent_bans = {}

    def is_enabled(self, chat_id: int) -> bool:
        return self.enabled_chats.get(chat_id, False)

    def toggle_status(self, chat_id: int, enable: bool):
        self.enabled_chats[chat_id] = enable
        if not enable:
            # Clear tracking data if disabled
            self.recent_bans.pop(chat_id, None)

    async def check_and_trigger_lockdown(self, client: Client, chat_id: int, actor_id: int):
        """
        Checks if ban threshold is met. If so, triggers lockdown.
        """
        now = datetime.now()
        
        # Initialize list for this chat if not exists
        if chat_id not in self.recent_bans:
            self.recent_bans[chat_id] = []
            
        # Add current ban timestamp
        self.recent_bans[chat_id].append(now)
        
        # Remove old timestamps outside the time window
        cutoff = now - timedelta(seconds=self.TIME_WINDOW)
        self.recent_bans[chat_id] = [t for t in self.recent_bans[chat_id] if t > cutoff]
        # Check if threshold exceeded
        if len(self.recent_bans[chat_id]) >= self.BAN_THRESHOLD:
            await self.execute_lockdown(client, chat_id, actor_id)
            # Reset counter after trigger to prevent loop
            self.recent_bans[chat_id] = []

    async def execute_lockdown(self, client: Client, chat_id: int, attacker_id: int):
        """
        Emergency Lockdown Protocol:
        1. Demote all admins (except bot itself).
        2. Lock chat permissions (no messages, no media).
        3. Kick the attacker if they are still present.
        """
        try:
            print(f"[AntiBanAll] LOCKDOWN TRIGGERED in Chat {chat_id} by User {attacker_id}")
            
            # 1. Send Alert
            await client.send_message(
                chat_id,
                "🚨 **EMERGENCY LOCKDOWN ACTIVATED** 🚨\n\n"
                "Mass ban activity detected. To protect the group:\n"
                "1. All Admins have been demoted.\n"
                "2. Chat has been locked.\n"
                "3. Attacker has been removed.\n\n"
                "Please contact the owner to restore access."
            )

            # 2. Demote All Admins
            # Get all administrators
            admins = await client.get_chat_members(chat_id, filter="administrators")
            
            bot_id = (await client.get_me()).id
            
            for admin in admins:
                user_id = admin.user.id
                # Do not demote the bot itself
                if user_id == bot_id:
                    continue
                
                try:
                    await client.promote_chat_member(
                        chat_id=chat_id,
                        user_id=user_id,
                        privileges=None # Removes all admin privileges
                    )
                    print(f"[AntiBanAll] Demoted admin: {user_id}")
                except Exception as e:
                    print(f"[AntiBanAll] Failed to demote {user_id}: {e}")

            # 3. Lock Chat Permissions
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

            # 4. Kick/Ban the Attacker
            try:
                await client.ban_chat_member(chat_id, attacker_id)
                print(f"[AntiBanAll] Banned attacker: {attacker_id}")
            except Exception as e:
                print(f"[AntiBanAll] Failed to ban attacker: {e}")

        except Exception as e:
            print(f"[AntiBanAll] Critical Error during lockdown: {e}")

# Instantiate Manager
anti_ban_mgr = AntiBanAllManager()

# --- HANDLERS ---

@app.on_message(filters.command("antibanall") & filters.group)
async def handle_antibanall_command(client, message):
    """
    Command: /antibanall enable | disable
    Only admins can use this.
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if user is admin
    member = await client.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await message.reply_text("❌ Only admins can configure Anti-Ban-All.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: `/antibanall enable` or `/antibanall disable`")
        return

    action = args[1].lower()
    
    if action == "enable":
        anti_ban_mgr.toggle_status(chat_id, True)
        await message.reply_text("✅ **Anti-Ban-All Enabled.**\nI will now monitor for mass bans and lock the chat if detected.")
    elif action == "disable":
        anti_ban_mgr.toggle_status(chat_id, False)
        await message.reply_text("❌ **Anti-Ban-All Disabled.**")
    else:
        await message.reply_text("Invalid argument. Use `enable` or `disable`.")

@app.on_chat_member_updated()
async def handle_member_update(client, update: ChatMemberUpdated):
    """
    Monitors changes in chat members.
    Detects when a user is banned/kicked.
    """
    chat_id = update.chat.id
    
    # Only process if Anti-Ban-All is enabled for this chat
    if not anti_ban_mgr.is_enabled(chat_id):
        return

    old_status = update.old_chat_member.status if update.old_chat_member else None
    new_status = update.new_chat_member.status if update.new_chat_member else None
    
    # Detect Ban/Kick: Member was present, now is banned/kicked/left
    # Note: Telegram API nuances vary. Usually, if someone is banned, 
    # their status changes to 'kicked' or they disappear from member list.
    # We look for transitions to 'KICKED' or 'BANNED'.
    
    is_banned = False
    actor_id = None
    
    if new_status:
        if new_status.status in [ChatMemberStatus.KICKED, ChatMemberStatus.BANNED]:
            is_banned = True
            # The actor who performed the ban is usually in update.from_user
            if update.from_user:
                actor_id = update.from_user.id
    
    # Alternative detection: If old status was member/admin and new is None (left/banned)
    # This depends on how Pyrogram reports it. 
    # For robustness, we rely on the explicit KICKED/BANNED status if available.
    
    if is_banned and actor_id:
        # Check if the actor is an admin (to distinguish between normal kick and mass ban attack)
        # If a normal user tries to ban, they can't. So actor is likely an admin or compromised account
        
        # Trigger the check
        await anti_ban_mgr.check_and_trigger_lockdown(client, chat_id, actor_id)

# Note: In some Pyrogram versions, on_chat_member_updated might not fire for every single ban 
# if done rapidly via API. If you find it missing events, you may need to use 
# @app.on_raw_update() and parse UpdateChannelParticipant manually, but that is complex.
# The above method works for standard UI-based bans.
