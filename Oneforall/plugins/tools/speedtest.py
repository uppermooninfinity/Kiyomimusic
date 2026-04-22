import asyncio
import speedtest

from pyrogram import filters
from pyrogram.types import Message

from Oneforall import app
from Oneforall.misc import SUDOERS

SPEED_VIDEO = "https://graph.org/file/308891fd6e656bcc70f0e-272ff13d24d1820cf5.mp4"


def run_speedtest():
    test = speedtest.Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    return test.results.dict()


@app.on_message(filters.command(["speedtest", "spt"]) & SUDOERS)
async def speedtest_function(client, message: Message):

    m = await message.reply_text("<blockquote>⚡ ʀᴜɴɴɪɴɢ ꜱᴘᴇᴇᴅ ᴛᴇꜱᴛ...</blockquote>")

    loop = asyncio.get_event_loop()

    try:
        result = await loop.run_in_executor(None, run_speedtest)
    except Exception as e:
        return await m.edit_text(f"<code>{e}</code>")

    # Convert to Mbps
    download = round(result["download"] / 1_000_000, 2)
    upload = round(result["upload"] / 1_000_000, 2)

    caption = f"""
<blockquote>
⚡ ꜱᴘᴇᴇᴅ ᴛᴇꜱᴛ ʀᴇꜱᴜʟᴛ ⚡

📡 ɪꜱᴘ: {result['client']['isp']}
🌍 ᴄᴏᴜɴᴛʀʏ: {result['client']['country']}

🖥️ ꜱᴇʀᴠᴇʀ: {result['server']['name']}
🏳️ ʟᴏᴄᴀᴛɪᴏɴ: {result['server']['country']} ({result['server']['cc']})
🏢 ꜱᴘᴏɴꜱᴏʀ: {result['server']['sponsor']}

📶 ᴘɪɴɢ: {result['ping']} ms
⬇️ ᴅᴏᴡɴʟᴏᴀᴅ: {download} Mbps
⬆️ ᴜᴘʟᴏᴀᴅ: {upload} Mbps
</blockquote>
"""
    try:
        await message.reply_video(
            video=SPEED_VIDEO,
            has_spoiler=True,
            caption=caption,
        )
    except Exception:
        await message.reply_text(caption)

    await m.delete()
