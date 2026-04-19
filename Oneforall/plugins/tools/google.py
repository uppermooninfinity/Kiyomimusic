import asyncio
import logging

from googlesearch import search
from pyrogram import filters
from SafoneAPI import SafoneAPI

from Oneforall import app


@app.on_message(filters.command(["google", "gle"]))
async def google(bot, message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Example:\n\n`/google lord ram`")

    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
    else:
        user_input = " ".join(message.command[1:])

    msg = await message.reply_text("**Searching on Google...**")

    try:
        results = await asyncio.to_thread(
            lambda: list(search(user_input, advanced=True, num_results=5))
        )

        if not results:
            return await msg.edit("No results found.")

        text = f"<b>Search Query:</b> {user_input}\n\n"

        for r in results:
            title = r.title or "No Title"
            url = r.url or ""
            desc = r.description or "No description"
            text += f"• <a href='{url}'>{title}</a>\n{desc}\n\n"

        await msg.edit(text, disable_web_page_preview=True)

    except Exception:
        logging.exception("Google search error")
        await msg.edit("Error while searching.")


@app.on_message(filters.command(["app", "apps"]))
async def app_search(bot, message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Example:\n\n`/app Free Fire`")

    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
    else:
        user_input = " ".join(message.command[1:])

    msg = await message.reply_text("**Searching on Play Store...**")

    try:
        data = await SafoneAPI().apps(user_input, 1)

        if not data or not data.get("results"):
            return await msg.edit("No app found.")

        app_data = data["results"][0]

        icon = app_data.get("icon")
        app_id = app_data.get("id", "N/A")
        link = app_data.get("link", "")
        desc = app_data.get("description", "No description")
        title = app_data.get("title", "Unknown")
        dev = app_data.get("developer", "Unknown")

        caption = (
            f"<b><a href='{link}'>{title}</a></b>\n\n"
            f"<b>ID:</b> <code>{app_id}</code>\n"
            f"<b>Developer:</b> {dev}\n\n"
            f"<b>Description:</b>\n{desc[:1000]}"
        )

        await message.reply_photo(icon, caption=caption)
        await msg.delete()

    except Exception:
        logging.exception("App search error")
        await msg.edit("Error while fetching app.")
