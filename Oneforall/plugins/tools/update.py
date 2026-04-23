import requests
from pyrogram import filters
from pyrogram.types import Message

from config import OWNER_ID
from Oneforall import app

# 🔧 CONFIG
GITHUB_REPO = "uppermooninfinity/kiyomimusic"
BRANCH = "main"
IMAGE_URL = "https://graph.org/file/5bf10b670c93c624af3e0-6d476603a36e8052b0.jpg"  # 🔥 put your image link

def load_last():
    try:
        with open("last_commit.txt") as f:
            return f.read().strip()
    except:
        return None

def save_last(sha):
    with open("last_commit.txt", "w") as f:
        f.write(sha)

LAST_COMMIT = load_last()


def get_commits():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{BRANCH}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    return res.json()


@app.on_message(filters.command("fetchupdate") & filters.user(OWNER_ID))
async def update_checker(_, message: Message):
    global LAST_COMMIT

    msg = await message.reply_text("🔍 Checking latest updates...")

    data = get_commits()
    if not data:
        return await msg.edit("❌ Failed to fetch commits.")

    latest_sha = data["sha"]

    if LAST_COMMIT is None:
        LAST_COMMIT = latest_sha
        save_last(latest_sha)
        return await msg.edit("✅ Tracking started. No updates yet.")

    if latest_sha == LAST_COMMIT:
        return await msg.edit("✅ No new updates.")

    # 🔥 New update
    commit_msg = data["commit"]["message"]
    author = data["commit"]["author"]["name"]
    url = data["html_url"]

    text = "⚪ Uᴘᴅᴀᴛᴇ ᴘʀ\n"
    text += f"- ᴏɴ ʙʀᴀɴᴄʜ {BRANCH}\n\n"

    for line in commit_msg.split("\n"):
        text += f": {line}\n"

    text += f"\n👤 {author}"
    text += f"\n🔗 {url}"
    text += "\n\n⛩️Stay tuned..."

    LAST_COMMIT = latest_sha
    save_last(latest_sha)

    # ❌ old message hata
    await msg.delete()

    # ✅ send with image
    await message.reply_photo(
        photo=IMAGE_URL,
        has_spoiler=True,
        caption=text
    )
