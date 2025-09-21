import os
from random import randint
from typing import Union
from pyrogram.types import InlineKeyboardMarkup
import asyncio
import ffmpeg

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


# 🔹 Helper: Apply Bass + Volume Boost
async def apply_bass_boost(input_file: str) -> str:
    output_file = f"processed_{os.path.basename(input_file)}.wav"
    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, af=config.BASS_BOOST, format="wav")
            .overwrite_output()
            .run(quiet=True)
        )
        return output_file
    except Exception as e:
        print(f"[FFMPEG ERROR] {e}")
        return input_file


# 🔹 Helper: Async pre-download for queue
async def preload_next_song(vidid, mystic, video):
    try:
        file_path, direct = await YouTube.download(vidid, mystic, video=video, videoid=True)
        return file_path, direct
    except:
        return None, None


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

    # --- Playlist handling ---
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(search, not spotify)
            except:
                continue
            if duration_min is None or duration_sec > config.DURATION_LIMIT:
                continue

            # Queue only if active
            if await is_active_chat(chat_id):
                await put_queue(chat_id, original_chat_id, f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n{_['play_20']} {position}\n\n"
                continue

            # If not active, start streaming immediately
            if not forceplay:
                db[chat_id] = []
            status = bool(video)

            # Async preload next song while current streams
            file_path, direct = await preload_next_song(vidid, mystic, status)
            if not file_path:
                continue

            processed_file = await apply_bass_boost(file_path)
            await Aviax.join_call(chat_id, original_chat_id, processed_file, video=status, image=thumbnail)
            await put_queue(chat_id, original_chat_id, processed_file if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            img = await gen_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

        if count == 0:
            return
        link = await AviaxBin(msg)
        lines = msg.count("\n")
        car = os.linesep.join(msg.split(os.linesep)[:17]) if lines >= 17 else msg
        carbon = await Carbon.generate(car, randint(100, 10000000))
        upl = close_markup(_)
        return await app.send_photo(original_chat_id, photo=carbon, caption=_["play_21"].format(position, link), reply_markup=upl)

    # --- YouTube / SoundCloud / Telegram / Live / Index Handling ---
    else:
        if streamtype in ["youtube", "soundcloud", "telegram", "live", "index"]:
            # Map result to file_path & metadata
            if streamtype == "youtube":
                vidid, link, title, duration_min, thumbnail = result["vidid"], result["link"], result["title"].title(), result["duration_min"], result["thumb"]
                status = bool(video)
                current_queue = db.get(chat_id)
                if current_queue and len(current_queue) >= 10:
                    return await app.send_message(original_chat_id, "You can't add more than 10 songs to the queue.")
                file_path, direct = await preload_next_song(vidid, mystic, status)
                if not file_path:
                    raise AssistantErr(_["play_14"])
            elif streamtype == "soundcloud":
                file_path, title, duration_min = result["filepath"], result["title"], result["duration_min"]
            elif streamtype == "telegram":
                file_path, link, title, duration_min = result["path"], result["link"], result["title"].title(), result["dur"]
                status = bool(video)
            elif streamtype == "live":
                vidid, link, title, thumbnail, duration_min = result["vidid"], result["link"], result["title"].title(), result["thumb"], "Live Track"
                status = bool(video)
                n, file_path = await YouTube.video(link)
                if n == 0:
                    raise AssistantErr(_["str_3"])
            elif streamtype == "index":
                file_path, title, duration_min = result, "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ", "00:00"

            # If chat already active, queue it
            if await is_active_chat(chat_id):
                if streamtype == "index":
                    await put_queue_index(chat_id, original_chat_id, "index_url", title, duration_min, user_name, file_path, "video" if video else "audio")
                else:
                    await put_queue(chat_id, original_chat_id, file_path, title, duration_min, user_name, vidid if 'vidid' in locals() else streamtype, user_id, "video" if video else "audio")
                position = len(db.get(chat_id)) - 1
                button = aq_markup(_, chat_id)
                await app.send_message(original_chat_id, _["queue_4"].format(position, title[:27], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
                return

            # Otherwise, start streaming
            if not forceplay:
                db[chat_id] = []

            # Apply bass boost for all non-index streams
            if streamtype != "index":
                file_path = await apply_bass_boost(file_path)

            if streamtype == "index":
                await Aviax.join_call(chat_id, original_chat_id, file_path, video=bool(video))
                await put_queue_index(chat_id, original_chat_id, "index_url", title, duration_min, user_name, file_path, "video" if video else "audio", forceplay=forceplay)
            else:
                await Aviax.join_call(chat_id, original_chat_id, file_path, video=bool(video), image=thumbnail if 'thumbnail' in locals() else None)
                await put_queue(chat_id, original_chat_id, file_path, title, duration_min, user_name, vidid if 'vidid' in locals() else streamtype, user_id, "video" if video else "audio", forceplay=forceplay)
                if video:
                    await add_active_video_chat(chat_id)

            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=thumbnail if 'thumbnail' in locals() else config.STREAM_IMG_URL, caption=_["stream_1"].format(link if 'link' in locals() else config.SUPPORT_GROUP, title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

