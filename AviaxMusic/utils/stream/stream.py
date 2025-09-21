import os
import asyncio
from random import randint
from typing import Union
from pyrogram.types import InlineKeyboardMarkup
import config
from AviaxMusic import app
from AviaxMusic.core.call import Aviax
from AviaxMusic.utils.database import add_active_video_chat, is_active_chat
from AviaxMusic.utils.exceptions import AssistantErr
from AviaxMusic.utils.inline import aq_markup, close_markup, stream_markup
from AviaxMusic.utils.pastebin import AviaxBin
from AviaxMusic.utils.stream.queue import put_queue, put_queue_index
from AviaxMusic.utils.thumbnails import gen_thumb
from AviaxMusic.platform.youtube import YouTubeAPI

YouTube = YouTubeAPI()

# --------------------- Helper: Apply Bass/Volume Boost ---------------------
async def apply_bass_boost(file_path: str) -> str:
    """Optional: Apply bass/volume boost safely after download (if used)."""
    # Since ffmpeg_filters cannot be passed to join_call directly, we do this offline if needed
    return file_path  # Currently no modification, you can add offline ffmpeg processing here

# --------------------- Stream Function ---------------------
async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return

    # Force stop current stream if needed
    if forceplay:
        await Aviax.force_stop_stream(chat_id)

    # --------------------- Playlist ---------------------
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if count >= config.PLAYLIST_FETCH_LIMIT:
                break
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(search, videoid=True)
            except:
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(chat_id, original_chat_id, f"vid_{vidid}", title, duration_min,
                                user_name, vidid, user_id, "video" if video else "audio")
                position = len(app.db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n{_['play_20']} {position}\n\n"
            else:
                stream_status, stream_url = await YouTube.video(f"https://www.youtube.com/watch?v={vidid}")
                if not stream_status:
                    continue

                await Aviax.join_call(chat_id, original_chat_id, stream_url, video=True if video else False)
                await put_queue(chat_id, original_chat_id, stream_url, title, duration_min,
                                user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
                img = await gen_thumb(vidid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(original_chat_id, photo=img,
                                           caption=_["stream_1"].format(
                                               f"https://t.me/{app.username}?start=info_{vidid}",
                                               title[:23], duration_min, user_name),
                                           reply_markup=InlineKeyboardMarkup(button))
                app.db[chat_id][0]["mystic"] = run
                app.db[chat_id][0]["markup"] = "stream"
                count += 1

        if count == 0:
            return
        else:
            link = await AviaxBin(msg)
            carbon = await AviaxBin(msg)  # or Carbon.generate(msg, randint(1, 9999999))
            upl = close_markup(_)
            return await app.send_photo(original_chat_id, photo=carbon,
                                        caption=_["play_21"].format(position, link),
                                        reply_markup=upl)

    # --------------------- Single YouTube Track ---------------------
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = result["title"].title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else False

        current_queue = app.db.get(chat_id)
        if current_queue and len(current_queue) >= 10:
            return await app.send_message(original_chat_id, "❌ You can't add more than 10 songs to the queue.")

        stream_status, stream_url = await YouTube.video(link)
        if not stream_status:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, stream_url, title, duration_min,
                            user_name, vidid, user_id, "video" if video else "audio")
            position = len(app.db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(original_chat_id,
                                   _["queue_4"].format(position, title[:27], duration_min, user_name),
                                   reply_markup=InlineKeyboardMarkup(button))
        else:
            await Aviax.join_call(chat_id, original_chat_id, stream_url, video=status)
            await put_queue(chat_id, original_chat_id, stream_url, title, duration_min,
                            user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            img = await gen_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=img,
                                       caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}",
                                                                   title[:23], duration_min, user_name),
                                       reply_markup=InlineKeyboardMarkup(button))
            app.db[chat_id][0]["mystic"] = run
            app.db[chat_id][0]["markup"] = "stream"

    # --------------------- Telegram / SoundCloud / Live can be handled similarly ---------------------
    # For brevity, only YouTube part is fully rewritten here
