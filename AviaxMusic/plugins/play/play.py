import asyncio
import yt_dlp
from pyrogram import filters
from pytgcalls.types.input_stream import AudioPiped

from AviaxMusic import app, Aviax  # core bot + pytgcalls instance


# Extract direct audio URL (no download)
async def get_stream_url(query: str):
    opts = {"format": "bestaudio", "quiet": True}
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
        return info["url"], info


@app.on_message(filters.command(["play", "vplay"]))
async def play_song(client, message):
    chat_id = message.chat.id
    user = message.from_user.mention if message.from_user else "Anonymous"

    if len(message.command) < 2:
        return await message.reply_text("❌ Give me something to play. Example: `/play song name or YouTube link`")

    query = message.text.split(" ", 1)[1]
    m = await message.reply_text("🔎 Searching...")

    # Case 1: YouTube Link
    if "youtube.com" in query or "youtu.be" in query:
        try:
            stream_url, info = await get_stream_url(query)
            title = info.get("title", "Unknown Title")

            await Aviax.join_group_call(
                chat_id,
                AudioPiped(stream_url),
                stream_type="pulse",
            )

            await m.edit_text(f"▶️ Playing instantly:\n**{title}**\n👤 Requested by {user}")
        except Exception as e:
            await m.edit_text(f"❌ Failed to play.\n`{type(e).__name__}: {e}`")
        return

    # Case 2: Telegram audio file
    if message.reply_to_message and message.reply_to_message.audio:
        try:
            file = await message.reply_to_message.download()
            await Aviax.join_group_call(
                chat_id,
                AudioPiped(file),
                stream_type="pulse",
            )
            await m.edit_text(f"▶️ Playing Telegram audio file\n👤 Requested by {user}")
        except Exception as e:
            await m.edit_text(f"❌ Failed: {type(e).__name__}")
        return

    # Case 3: Search query (YouTube search)
    try:
        search_url = f"ytsearch1:{query}"
        stream_url, info = await get_stream_url(search_url)
        title = info.get("title", "Unknown Title")

        await Aviax.join_group_call(
            chat_id,
            AudioPiped(stream_url),
            stream_type="pulse",
        )
        await m.edit_text(f"▶️ Playing:\n**{title}**\n👤 Requested by {user}")
    except Exception as e:
        await m.edit_text(f"❌ Could not fetch.\n`{type(e).__name__}: {e}`")
