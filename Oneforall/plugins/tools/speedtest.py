import asyncio
import speedtest

from pyrogram import filters
from pyrogram.types import Message

from Oneforall import app
from Oneforall.misc import SUDOERS

SPEED_GIF = "CgACAgUAAxkBAAEdaG1p6H47oioRZS4hUIqfVsWzUCVRdwACgh4AAqqjcVUD4vp5nyew_DsE" 


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

    download = round(result["download"] / 1_000_000, 2)
    upload = round(result["upload"] / 1_000_000, 2)

    caption = f"""
<blockquote>
⚡ ꜱᴘᴇᴇᴅ ᴛᴇꜱᴛ ʀᴇꜱᴜʟᴛꜱ ⚡

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

    await message.reply_animation(
        animation=SPEED_GIF,
        caption=caption
    )

    await m.delete()
