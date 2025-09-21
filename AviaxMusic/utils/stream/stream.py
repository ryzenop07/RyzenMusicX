import os
import asyncio
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from AviaxMusic import Carbon, YouTube, app
from AviaxMusic.core.call import Aviax
from AviaxMusic.misc import db
from AviaxMusic.utils.database import add_active_video_chat, is_active_chat
from AviaxMusic.utils.exceptions import AssistantErr
from AviaxMusic.utils.inline import aq_markup, close_markup, stream_markup
from AviaxMusic.utils.pastebin import AviaxBin
from AviaxMusic.utils.stream.queue import put_queue, put_queue_index
from AviaxMusic.utils.thumbnails import gen_thumb

# 🔹 Helper: Apply on-the-fly FFmpeg filters
def ffmpeg_opts():
    return config.BASS_BOOST if hasattr(config, "BASS_BOOST") else None

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

    if forceplay:
        await Aviax.force_stop_stream(chat_id)

    async def add_to_queue(file, title, dur, vidid=None, streamtype_local="audio"):
        """Add song to queue instantly"""
        await put_queue(
            chat_id,
            original_chat_id,
            file,
            title,
            dur,
            user_name,
            vidid if vidid else streamtype_local,
            user_id,
            "video" if video else "audio",
            forceplay=forceplay,
        )

    # 🔹 PLAYLIST
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if str(duration_min) == "None" or duration_sec > config.DURATION_LIMIT:
                continue

            # 🔹 Instant queue insert if song already playing
            if await is_active_chat(chat_id):
                await add_to_queue(f"vid_{vidid}", title, duration_min, vidid)
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n{_['play_20']} {position}\n\n"
            else:
                file_path, direct = await YouTube.download(vidid, mystic, video=True if video else None, videoid=True)
                # 🔹 Stream directly with FFmpeg filters
                await Aviax.join_call(chat_id, original_chat_id, file_path, video=True if video else None, ffmpeg_filters=ffmpeg_opts())
                await add_to_queue(file_path if direct else f"vid_{vidid}", title, duration_min, vidid)
                img = await gen_thumb(vidid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        if count == 0:
            return
        else:
            link = await AviaxBin(msg)
            carbon = await Carbon.generate(msg, randint(100, 10000000))
            upl = close_markup(_)
            return await app.send_photo(original_chat_id, photo=carbon, caption=_["play_21"].format(position, link), reply_markup=upl)

    # 🔹 YOUTUBE / SOUND / TELEGRAM / LIVE / INDEX
    elif streamtype in ["youtube", "soundcloud", "telegram", "live", "index"]:
        # Simplified logic: direct streaming + instant queue
        if streamtype == "youtube":
            link = result["link"]
            vidid = result["vidid"]
            title = (result["title"]).title()
            duration_min = result["duration_min"]
            thumbnail = result["thumb"]
            status = True if video else None
            file_path, direct = await YouTube.download(vidid, mystic, videoid=True, video=status)

        elif streamtype == "soundcloud":
            file_path = result["filepath"]
            title = result["title"]
            duration_min = result["duration_min"]
            status = None

        elif streamtype == "telegram":
            file_path = result["path"]
            title = (result["title"]).title()
            duration_min = result["dur"]
            status = True if video else None

        elif streamtype == "live":
            link = result["link"]
            vidid = result["vidid"]
            title = (result["title"]).title()
            duration_min = "Live Track"
            thumbnail = result.get("thumb")
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            status = True if video else None

        elif streamtype == "index":
            file_path = result
            title = "Index / m3u8 Link"
            duration_min = "00:00"
            status = True if video else None

        # 🔹 Instant queue insert if playing
        if await is_active_chat(chat_id):
            await add_to_queue(file_path if 'file_path' in locals() else file_path, title, duration_min, vidid if 'vidid' in locals() else None, streamtype)
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:27], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
            await Aviax.join_call(chat_id, original_chat_id, file_path if 'file_path' in locals() else file_path, video=status, ffmpeg_filters=ffmpeg_opts(), image=thumbnail if 'thumbnail' in locals() else None)
            await add_to_queue(file_path if 'file_path' in locals() else file_path, title, duration_min, vidid if 'vidid' in locals() else None, streamtype)
            if video and streamtype == "telegram":
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=thumbnail if 'thumbnail' in locals() else config.STREAM_IMG_URL, caption=_["stream_1"].format(link if 'link' in locals() else file_path, title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
