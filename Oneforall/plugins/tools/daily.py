import time
from pyrogram import filters
from Oneforall import app
from Oneforall.mongo import db

# Collections
ECONOMY_COLL = db.roshni_economy

@app.on_message(filters.command("daily"))
async def daily_cmd(client, message):
    user_id = message.from_user.id
    is_premium = getattr(message.from_user, "is_premium", False)

    try:
        # Fetch user data to check health/death status
        user_data = await ECONOMY_COLL.find_one({"user_id": user_id}) or {}
        
        # BAKA CHECK: If dead, no daily rewards
        if user_data.get("is_dead", False):
            return await message.reply(
                "💀 **ʏᴏᴜ ᴀʀᴇ ᴅᴇᴀᴅ, ʙᴀᴋᴀ!**\n"
                "_ɢʜᴏsᴛs ᴄᴀɴ'ᴛ ᴄᴏʟʟᴇᴄᴛ ʙʟᴇssɪɴɢs. ᴜsᴇ /revive ꜰɪʀsᴛ._"
            )

        last_daily = user_data.get("last_daily", 0)
        balance = user_data.get("balance", 0)

        current_time = time.time()
        if current_time - last_daily < 86400:
            remaining = 86400 - (current_time - last_daily)
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            return await message.reply(
                f"⏳ **ʟᴏᴠᴇ, ᴄᴏᴍᴇ ʙᴀᴄᴋ ɪɴ `{hours}ʜ {mins}ᴍ`**"
            )

        amount = 2000 if is_premium else 1000
        new_balance = balance + amount

        await ECONOMY_COLL.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "balance": new_balance,
                    "last_daily": current_time
                }
            },
            upsert=True
        )

        await message.reply(
            "🎀 **ʀᴏsʜɴɪ’ꜱ ᴅᴀɪʟʏ ʙʟᴇssɪɴɢ**\n\n"
            f"💰 sʜᴇ sᴍɪʟᴇᴅ ᴜᴘᴏɴ ʏᴏᴜ · `+${amount:,}`\n"
            f"💳 ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ · `${new_balance:,}`\n\n"
            "✿ _sᴘᴇɴᴅ ɪᴛ ᴡɪsᴇʟʏ, sᴡᴇᴇᴛʜᴇᴀʀᴛ_"
        )

    except Exception as e:
        print(f"Daily Error: {e}")
        await message.reply("❌ **ᴇʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ᴅᴀɪʟʏ.**")
      
