import asyncio
from typing import Union
from pyrogram.types import InlineKeyboardMarkup

from AviaxMusic import app
from AviaxMusic.misc import db
from AviaxMusic.utils.stream.queue import put_queue, put_queue_index
from AviaxMusic.core.call import Aviax
from AviaxMusic.utils.thumbnails import gen_thumb
from AviaxMusic.utils.inline import aq_markup, stream_markup, close_markup


async def stream(_, mystic, user_id, result, chat_id, user_name, original_chat_id,
                 video: Union[bool, str] = None, streamtype: Union[bool, str] = None,
                 spotify: Union[bool, str] = None, forceplay: Union[bool, str] = None):

    if not result:
        return

    # Stop current call if forceplay
    if forceplay:
        await Aviax.force_stop_stream(chat_id)

    # Fast queue insertion
    if await Aviax.is_playing(chat_id):
        # If a song is already playing, just add to queue instantly
        if streamtype in ["youtube", "soundcloud", "telegram", "live", "index"]:
            await put_queue(
                chat_id,
                original_chat_id,
                result.get("file") or result.get("link"),
                result.get("title") or "Unknown",
                result.get("duration_min") or "00:00",
                user_name,
                result.get("vidid") or "link",
                user_id,
                "video" if video else "audio",
                forceplay=forceplay
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, result.get("title")[:27], result.get("duration_min"), user_name),
                reply_markup=InlineKeyboardMarkup(button)
            )
            return  # exit, song added to queue instantly

    # Else: play immediately
    # Use direct stream if available, skip processing for speed
    file_path = result.get("file") or result.get("link")
    title = result.get("title") or "Unknown"
    duration_min = result.get("duration_min") or "00:00"
    thumbnail = result.get("thumb") or None
    status = True if video else None

    # Start streaming instantly
    await Aviax.join_call(chat_id, original_chat_id, file_path, video=status, image=thumbnail)

    # Add to queue for tracking
    await put_queue(
        chat_id,
        original_chat_id,
        file_path,
        title,
        duration_min,
        user_name,
        result.get("vidid") or "link",
        user_id,
        "video" if video else "audio",
        forceplay=forceplay
    )

    # Generate thumbnail async without blocking playback
    asyncio.create_task(gen_thumb(result.get("vidid")))

    # Send info message
    button = stream_markup(_, chat_id)
    run = await app.send_photo(
        original_chat_id,
        photo=thumbnail or "https://telegra.ph/file/default.png",
        caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{result.get('vidid')}", title[:23], duration_min, user_name),
        reply_markup=InlineKeyboardMarkup(button),
    )

    db[chat_id][0]["mystic"] = run
    db[chat_id][0]["markup"] = "stream"
