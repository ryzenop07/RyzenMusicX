import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup

from AviaxMusic.utils.stream.queue import put_queue
from AviaxMusic.misc import db
from AviaxMusic.utils.inline.play import aq_markup
from AviaxMusic.platforms.Youtube import YouTubeAPI
from config import autoclean

# Assume Aviax is your voice call manager
from AviaxMusic.core.call import Aviax


@Client.on_message(filters.command(["play", "vplay", "cplay"]))
async def play_handler(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.mention

    query = ""
    if len(message.command) > 1:
        query = message.text.split(None, 1)[1]
    elif message.reply_to_message and message.reply_to_message.audio:
        query = message.reply_to_message.audio.file_id
    else:
        await message.reply("❌ Please provide a song name or link.")
        return

    video = "vplay" in message.command  # detect if video play requested
    forceplay = "cplay" in message.command

    yt = YouTubeAPI()

    try:
        # Fetch song details
        if "youtube.com" in query or "youtu.be" in query:
            title, duration_min, duration_sec, thumb, vidid = await yt.details(query)
            file, direct = await yt.download(query, message)
        else:
            # Treat as search query
            title, duration_min, duration_sec, thumb, vidid = await yt.details(query)
            file, direct = await yt.download(f"https://www.youtube.com/watch?v={vidid}", message)

    except Exception as e:
        await message.reply(f"❌ Failed to fetch song: {e}")
        return

    # ✅ FAST QUEUE: if something already playing
    if db.get(chat_id) and len(db[chat_id]) > 0:
        await put_queue(
            chat_id,
            chat_id,
            file,
            title,
            duration_min,
            user_name,
            vidid,
            user_id,
            "video" if video else "audio",
            forceplay=forceplay,
        )
        pos = len(db.get(chat_id)) - 1
        buttons = aq_markup("en", chat_id)
        await message.reply_text(
            f"🎶 Added to queue at position #{pos}\n\n**{title[:40]}**\n⏱️ {duration_min} | 👤 {user_name}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # ✅ Nothing playing: Start instantly
    try:
        await Aviax.join_call(
            chat_id,
            file,
            video=video,
        )
        await put_queue(
            chat_id,
            chat_id,
            file,
            title,
            duration_min,
            user_name,
            vidid,
            user_id,
            "video" if video else "audio",
            forceplay=True,
        )

        buttons = aq_markup("en", chat_id)
        await message.reply_text(
            f"▶️ Now playing\n\n**{title[:40]}**\n⏱️ {duration_min} | 👤 {user_name}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception as e:
        await message.reply(f"⚠️ Failed to start playback: {e}")
        return
