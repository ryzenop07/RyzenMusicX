import os
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

    # ---------------- PLAYLIST ----------------
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if count >= config.PLAYLIST_FETCH_LIMIT:
                break
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if duration_min is None or duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id, original_chat_id, f"vid_{vidid}", title, duration_min,
                    user_name, vidid, user_id, "video" if video else "audio"
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(vidid, mystic, video=status, videoid=True)
                except:
                    raise AssistantErr(_["play_14"])

                processed_file = await apply_bass_boost(file_path)

                await Aviax.join_call(chat_id, original_chat_id, processed_file, video=status, image=thumbnail)
                await put_queue(
                    chat_id, original_chat_id, processed_file if direct else f"vid_{vidid}", 
                    title, duration_min, user_name, vidid, user_id, "video" if video else "audio",
                    forceplay=forceplay
                )

                img = await gen_thumb(vidid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    original_chat_id, photo=img,
                    caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], duration_min, user_name),
                    reply_markup=InlineKeyboardMarkup(button)
                )
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

    # ---------------- YOUTUBE ----------------
    elif streamtype == "youtube":
        link, vidid, title, duration_min, thumbnail = result["link"], result["vidid"], result["title"].title(), result["duration_min"], result["thumb"]
        status = True if video else None

        if db.get(chat_id) is not None and len(db.get(chat_id)) >= 10:
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

    # ---------------- SOUNDCLOUD ----------------
    elif streamtype == "soundcloud":
        file_path, title, duration_min = result["filepath"], result["title"], result["duration_min"]
        processed_file = await apply_bass_boost(file_path)

        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, processed_file, title, duration_min, user_name, streamtype, user_id, "audio")
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:27], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
            await Aviax.join_call(chat_id, original_chat_id, processed_file, video=None)
            await put_queue(chat_id, original_chat_id, processed_file, title, duration_min, user_name, streamtype, user_id, "audio", forceplay=forceplay)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=config.SOUNCLOUD_IMG_URL, caption=_["stream_1"].format(config.SUPPORT_GROUP, title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    # ---------------- TELEGRAM ----------------
    elif streamtype == "telegram":
        file_path, link, title, duration_min = result["path"], result["link"], result["title"].title(), result["dur"]
        status = True if video else None

        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, file_path, title, duration_min, user_name, streamtype, user_id, "video" if video else "audio")
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:27], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []

            processed_file = await apply_bass_boost(file_path)

            await Aviax.join_call(chat_id, original_chat_id, processed_file, video=status)
            await put_queue(chat_id, original_chat_id, processed_file, title, duration_min, user_name, streamtype, user_id, "video" if video else "audio", forceplay=forceplay)
            if video:
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL, caption=_["stream_1"].format(link, title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    # ---------------- LIVE ----------------
    elif streamtype == "live":
        link, vidid, title, thumbnail = result["link"], result["vidid"], result["title"].title(), result["thumb"]
        duration_min = "Live Track"
        status = True if video else None

        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, f"live_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:27], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])

            processed_file = await apply_bass_boost(file_path)

            await Aviax.join_call(chat_id, original_chat_id, processed_file, video=status, image=thumbnail)
            await put_queue(chat_id, original_chat_id, f"live_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            img = await gen_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    # ---------------- INDEX ----------------
    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"

        if await is_active_chat(chat_id):
            await put_queue_index(chat_id, original_chat_id, "index_url", title, duration_min, user_name, link, "video" if video else "audio")
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await mystic.edit_text(text=_["queue_4"].format(position, title[:27], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
            await Aviax.join_call(chat_id, original_chat_id, link, video=True if video else None)
            await put_queue_index(chat_id, original_chat_id, "index_url", title, duration_min, user_name, link, "video" if video else "audio", forceplay=forceplay)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(original_chat_id, photo=config.STREAM_IMG_URL, caption=_["stream_2"].format(user_name), reply_markup=InlineKeyboardMarkup(button))
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
