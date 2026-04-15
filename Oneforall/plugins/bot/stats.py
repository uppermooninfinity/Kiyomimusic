import platform
import asyncio
from sys import version as pyver
from io import BytesIO

import psutil
import matplotlib.pyplot as plt

from pyrogram import __version__ as pyrover, filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message, CallbackQuery

try:
    from pytgcalls import __version__ as pytgver
except:
    pytgver = "Unknown"

import config
from config import BANNED_USERS
from Oneforall import app
from Oneforall.core.userbot import assistants
from Oneforall.misc import SUDOERS, mongodb
from Oneforall.plugins import ALL_MODULES
from Oneforall.utils.database import (
    get_queries,
    get_served_chats,
    get_served_users,
    get_sudoers,
)
from Oneforall.utils.decorators.language import language, languageCB
from Oneforall.utils.inline.stats import back_stats_buttons, stats_buttons


async def generate_cpu_graph():
    usage = []
    for _ in range(10):
        usage.append(psutil.cpu_percent(interval=0.2))

    plt.figure()
    plt.plot(usage)
    plt.title("CPU Usage (%)")
    plt.xlabel("Time")
    plt.ylabel("Usage")

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    return buffer


@app.on_message(filters.command(["stats", "gstats"]) & filters.group & ~BANNED_USERS)
@language
async def stats_global(client, message: Message, _):
    upl = stats_buttons(_, message.from_user.id in SUDOERS)

    await message.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("stats_back") & ~BANNED_USERS)
@languageCB
async def home_stats(client, query: CallbackQuery, _):
    upl = stats_buttons(_, query.from_user.id in SUDOERS)

    await query.edit_message_text(
        text=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("TopOverall") & ~BANNED_USERS)
@languageCB
async def overall_stats(client, query: CallbackQuery, _):
    await query.answer()

    upl = back_stats_buttons(_)

    served_chats, served_users, total_queries = await asyncio.gather(
        get_served_chats(),
        get_served_users(),
        get_queries(),
    )

    text = _["gstats_3"].format(
        app.mention,
        len(assistants),
        len(BANNED_USERS),
        len(served_chats),
        len(served_users),
        total_queries,
        len(ALL_MODULES),
        len(SUDOERS),
        config.AUTO_LEAVING_ASSISTANT,
        config.DURATION_LIMIT_MIN,
    )

    graph = await generate_cpu_graph()

    await query.message.reply_photo(
        photo=graph,
        caption=text,
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("bot_stats_sudo") & ~BANNED_USERS)
@languageCB
async def bot_stats(client, query: CallbackQuery, _):
    if query.from_user.id not in SUDOERS:
        return await query.answer(_["gstats_4"], show_alert=True)

    await query.answer()
    upl = back_stats_buttons(_)

    tasks = await asyncio.gather(
        get_served_chats(),
        get_served_users(),
        get_sudoers(),
    )

    served_chats = len(tasks[0])
    served_users = len(tasks[1])
    sudoers_count = len(tasks[2])

    p_core = psutil.cpu_count(logical=False) or 0
    t_core = psutil.cpu_count(logical=True) or 0

    ram = f"{round(psutil.virtual_memory().total / (1024.0**3), 2)} GB"

    cpu_percent = psutil.cpu_percent(interval=0.5)

    cpu_freq = "Unavailable"
    try:
        freq = psutil.cpu_freq()
        if freq and freq.current:
            cpu_freq = f"{round(freq.current/1000,2)} GHz"
    except:
        pass

    hdd = psutil.disk_usage("/")
    total = round(hdd.total / (1024.0**3), 2)
    used = round(hdd.used / (1024.0**3), 2)
    free = round(hdd.free / (1024.0**3), 2)

    try:
        call = await mongodb.command("dbstats")
        datasize = round(call.get("dataSize", 0) / 1024, 2)
        storage = round(call.get("storageSize", 0) / 1024, 2)
        collections = call.get("collections", 0)
        objects = call.get("objects", 0)
    except:
        datasize = storage = collections = objects = 0

    text = _["gstats_5"].format(
        app.mention,
        len(ALL_MODULES),
        platform.system(),
        ram,
        p_core,
        t_core,
        f"{cpu_freq} ({cpu_percent}%)",
        pyver.split()[0],
        pyrover,
        pytgver,
        total,
        used,
        free,
        served_chats,
        served_users,
        len(BANNED_USERS),
        sudoers_count,
        datasize,
        storage,
        collections,
        objects,
    )

    graph = await generate_cpu_graph()

    await query.message.reply_photo(
        photo=graph,
        caption=text,
        reply_markup=upl,
                       )
