import os
import tempfile
import shutil
from random import randint
from typing import Union

import ffmpeg
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


# ---------------- Helper: Apply Bass + Volume Boost ----------------
async def apply_bass_boost(input_file: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp_file_path = tmp_file.name
    tmp_file.close()
    try:
        (
            ffmpeg
            .input(input_file)
            .output(tmp_file_path, af=config.BASS_BOOST, format="mp3")
            .overwrite_output()
            .run(quiet=True)
        )
        return tmp_file_path
    except Exception as e:
        print(f"[FFMPEG ERROR] {e}")
        return input_file  # fallback if processing fails


# ---------------- Stream Function ----------------
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

    # ---------------- Playlist Stream ----------------
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

            if await is_active_chat(chat_id):
                await put_queue(chat_id, original_chat_id, f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(vidid, mystic, video=status, videoid=True)
                except:
                    raise AssistantErr(_["play_14"])

                # Apply Bass Boost
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
        else:
            link = await AviaxBin(msg)
            lines = msg.count("\n")
            car = os.linesep.join(msg.split(os.linesep)[:17]) if lines >= 17 else msg
            carbon = await Carbon.generate(car, randint(100, 10000000))
            upl = close_markup(_)
            return await app.send_photo(original_chat_id, photo=carbon, caption=_["play_21"].format(position, link), reply_markup=upl)

    # ---------------- YouTube Stream ----------------
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None

        current_queue = db.get(chat_id)
        if current_queue is not None and len(current_queue) >= 10:
            return await app.send_message(original_chat_id, "You can't add more than 10 songs to the queue.")

        try:
            file_path, direct = await YouTube.download(vidid, mystic, videoid=True, video=status)
        except:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:27], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []

            processed_file = await apply_bass_boost(file_path)
            await Aviax.join_call(chat_id, original_chat_id, processed_file, video=status, image=thumbnail)
            await put_queue(chat_id, original_chat_id, processed_file if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            img = await gen_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

    # ---------------- Other Stream Types ----------------
    # soundcloud / telegram / live / index
    # You can repeat the same approach:
    # 1. Download or get file path
    # 2. Apply bass boost: processed_file = await apply_bass_boost(file_path)
    # 3. Pass processed_file to Aviax.join_call
    # 4. Update queue and send inline buttons

