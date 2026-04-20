import aiohttp
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from Oneforall import app

ANILIST_API = "https://graphql.anilist.co"


# ─── HELP ───
__HELP__ = """
✦ Anime Module:

✧ /anime - Get information on a specific anime using keywords or Anilist ID.
✧ /anilist - Choose between multiple anime results.
✧ /character - Get character info.
✧ /manga - Get manga info.
✧ /airing - Check airing status.
✧ /top - Get top anime.
✧ /user - Get Anilist user info.
✧ /fillers - Get filler episodes.
"""


# ─── API REQUEST ───
async def fetch_anilist(query, variables):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            ANILIST_API, json={"query": query, "variables": variables}
        ) as resp:
            return await resp.json()


# ─── ANIME COMMAND ───
@app.on_message(filters.command("anime"))
async def anime_cmd(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Give anime name.")

    search = " ".join(message.command[1:])

    query = """
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        id
        title {
          romaji
          english
        }
        description
        episodes
        status
        averageScore
        bannerImage
        coverImage {
          large
        }
      }
    }
    """

    data = await fetch_anilist(query, {"search": search})

    if "data" not in data or not data["data"]["Media"]:
        return await message.reply("❌ Anime not found.")

    media = data["data"]["Media"]

    title = media["title"]["english"] or media["title"]["romaji"]
    desc = media["description"] or "No description"
    desc = desc.replace("<br>", "").replace("<i>", "").replace("</i>", "")

    text = f"""
🎬 **{title}**

📺 Episodes: {media['episodes']}
📊 Score: {media['averageScore']}
📡 Status: {media['status']}

📝 {desc[:400]}...
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔍 More Like This",
                    callback_data=f"similar_{media['id']}",
                )
            ]
        ]
    )

    await message.reply_photo(
        media["coverImage"]["large"],
        caption=text,
        reply_markup=buttons,
    )


# ─── ANILIST MULTI SEARCH ───
@app.on_message(filters.command("anilist"))
async def anilist_cmd(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Give anime name.")

    search = " ".join(message.command[1:])

    query = """
    query ($search: String) {
      Page(perPage: 5) {
        media(search: $search, type: ANIME) {
          id
          title {
            romaji
          }
        }
      }
    }
    """

    data = await fetch_anilist(query, {"search": search})
    results = data["data"]["Page"]["media"]

    if not results:
        return await message.reply("❌ No results found.")

    buttons = []
    for anime in results:
        buttons.append(
            [
                InlineKeyboardButton(
                    anime["title"]["romaji"],
                    callback_data=f"anime_{anime['id']}",
                )
            ]
        )

    await message.reply(
        "🔎 Select an anime:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ─── CALLBACK FOR SELECTED ANIME ───
@app.on_callback_query(filters.regex("^anime_"))
async def anime_callback(_, query: CallbackQuery):
    anime_id = int(query.data.split("_")[1])

    query_api = """
    query ($id: Int) {
      Media(id: $id, type: ANIME) {
        title {
          romaji
        }
        description
        episodes
        averageScore
        coverImage {
          large
        }
      }
    }
    """

    data = await fetch_anilist(query_api, {"id": anime_id})
    media = data["data"]["Media"]

    title = media["title"]["romaji"]
    desc = (media["description"] or "").replace("<br>", "")

    text = f"""
🎬 **{title}**

📺 Episodes: {media['episodes']}
📊 Score: {media['averageScore']}

📝 {desc[:400]}...
"""

    await query.message.edit_media(
        media={
            "type": "photo",
            "media": media["coverImage"]["large"],
            "caption": text,
        }
    )


# ─── CHARACTER ───
@app.on_message(filters.command("character"))
async def character_cmd(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Give character name.")

    name = " ".join(message.command[1:])

    query = """
    query ($search: String) {
      Character(search: $search) {
        name {
          full
        }
        description
        image {
          large
        }
      }
    }
    """

    data = await fetch_anilist(query, {"search": name})
    char = data["data"]["Character"]

    desc = (char["description"] or "").replace("<br>", "")

    await message.reply_photo(
        char["image"]["large"],
        caption=f"👤 **{char['name']['full']}**\n\n{desc[:400]}...",
    )


# ─── MANGA ───
@app.on_message(filters.command("manga"))
async def manga_cmd(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Give manga name.")

    name = " ".join(message.command[1:])

    query = """
    query ($search: String) {
      Media(search: $search, type: MANGA) {
        title {
          romaji
        }
        chapters
        averageScore
        coverImage {
          large
        }
      }
    }
    """

    data = await fetch_anilist(query, {"search": name})
    media = data["data"]["Media"]

    await message.reply_photo(
        media["coverImage"]["large"],
        caption=f"📖 **{media['title']['romaji']}**\n\nChapters: {media['chapters']}\nScore: {media['averageScore']}",
    )


# ─── TOP ANIME ───
@app.on_message(filters.command("top"))
async def top_cmd(_, message: Message):
    query = """
    query {
      Page(perPage: 5) {
        media(type: ANIME, sort: SCORE_DESC) {
          title {
            romaji
          }
          averageScore
        }
      }
    }
    """

    data = await fetch_anilist(query, {})
    results = data["data"]["Page"]["media"]

    text = "🏆 **Top Anime:**\n\n"
    for i, anime in enumerate(results, 1):
        text += f"{i}. {anime['title']['romaji']} — {anime['averageScore']}\n"

    await message.reply(text)
