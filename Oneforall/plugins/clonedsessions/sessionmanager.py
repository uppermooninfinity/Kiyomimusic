from pyrogram import Client
from Oneforall.plugins.pmguard import PMGuard

API_ID = 21762522
API_HASH = "46800c1e399367a29d39554feedbe741"

active_clients = {}
active_pmguard = {}


async def start_session(user_id: int, session_string: str):

    if user_id in active_clients:
        return False, "⚠️ Session already running"

    try:

        # clean session string
        session_string = session_string.strip().replace("\n", "").replace(" ", "")

        client = Client(
            name=f"session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string
        )

        await client.start()

        me = await client.get_me()

        # load PMGuard
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

        await client.stop()

        active_clients.pop(user_id, None)
        active_pmguard.pop(user_id, None)

        return True, "🛑 Session stopped successfully"

    except Exception as e:
        return False, f"❌ Error:\n{str(e)}"


def get_active_sessions():
    return list(active_clients.keys())
