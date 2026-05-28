import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from pyrogram import Client as PyroClient

from Oneforall.plugins.pmguard import PMGuard

API_ID = 21762522
API_HASH = "46800c1e399367a29d39554feedbe741"

active_clients = {}
active_pmguard = {}


def detect_session_type(session: str):

    if not session:
        return "invalid"

    # Telethon sessions are usually long base64-like strings
    if len(session) > 150 and not session.startswith("BQ"):
        return "telethon"

    # Pyrogram sessions often shorter / different encoding
    return "pyrogram"


async def start_session(user_id: int, session_string: str):

    if user_id in active_clients:
        return False, "⚠️ Session already running"

    session_type = detect_session_type(session_string)

    try:

        # =========================
        # TELETHON SESSION
        # =========================
        if session_type == "telethon":

            client = TelegramClient(
                StringSession(session_string),
                API_ID,
                API_HASH
            )

        # =========================
        # PYROGRAM SESSION
        # =========================
        elif session_type == "pyrogram":

            client = PyroClient(
                name=f"session_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_string
            )

        else:
            return False, "❌ Invalid session format"

        await client.start()

        me = await client.get_me()

        # =========================
        # LOAD PM GUARD
        # =========================
        pmguard = PMGuard(client, user_id)
        pmguard.load()

        active_clients[user_id] = client
        active_pmguard[user_id] = pmguard

        return True, f"✅ Session started for {me.first_name}"

    except Exception as e:
        return False, f"❌ Failed:\n{str(e)}"


async def stop_session(user_id: int):

    client = active_clients.get(user_id)

    if not client:
        return False, "❌ No active session"

    try:

        await client.disconnect()

        active_clients.pop(user_id, None)
        active_pmguard.pop(user_id, None)

        return True, "🛑 Session stopped successfully"

    except Exception as e:
        return False, f"❌ Error:\n{str(e)}"


def get_active_sessions():

    return list(active_clients.keys())
