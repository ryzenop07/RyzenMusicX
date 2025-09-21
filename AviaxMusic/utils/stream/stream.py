import os
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

    async def join_call(file_path, thumbnail=None, is_video=None):
        """
        Join voice call instantly with optional live filters.
        Applies bass/volume boost on-the-fly.
        """
        filters = config.LIVE_AUDIO_FILTER if not is_video else None
        await Aviax.join_call(
            chat_id,
            original_chat_id,
            file_path,
            video=is_video,
            image=thumbnail,
            ffmpeg_filters=filters,  # Live audio filters for bass/volume
        )

    # ---------------- PLAYLIST ----------------
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if count >= config.PLAYLIST_FETCH_LIMIT:
                break
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(
                    search, False if spotify else True
                )
            except:
                continue
            if str(duration_min) == "None" or duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                count += 1
                position = len(db.get(chat_id)) - 1
                msg += f"{count}. {title[:70]}\n{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []

                file_path, direct = await YouTube.download(
                    vidid, mystic, video=True if video else None, videoid=True
                )

                await join_call(file_path, thumbnail, video)
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )
                img = await gen_thumb(vidid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:23],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        if count == 0:
            return
        link = await AviaxBin(msg)
        lines = msg.count("\n")
        car = os.linesep.join(msg.split(os.linesep)[:17]) if lines >= 17 else msg
        carbon = await Carbon.generate(car, randint(100, 10000000))
        upl = close_markup(_)
        return await app.send_photo(
            original_chat_id,
            photo=carbon,
            caption=_["play_21"].format(position, link),
            reply_markup=upl,
        )

    # ---------------- SINGLE TRACK ----------------
    if streamtype in ["youtube", "soundcloud", "telegram", "live", "index"]:
        if streamtype == "youtube":
            file_path, direct = await YouTube.download(
                result["vidid"], mystic, video=True if video else None, videoid=True
            )
            title = result["title"].title()
            duration_min = result["duration_min"]
            thumbnail = result["thumb"]
            stream_name = f"vid_{result['vidid']}"
        elif streamtype == "soundcloud":
            file_path = result["filepath"]
            title = result["title"]
            duration_min = result["duration_min"]
            stream_name = "soundcloud"
            thumbnail = config.SOUNCLOUD_IMG_URL
        elif streamtype == "telegram":
            file_path = result["path"]
            title = result["title"].title()
            duration_min = result["dur"]
            stream_name = "telegram"
            thumbnail = config.TELEGRAM_AUDIO_URL
        elif streamtype == "live":
            file_path = result["link"]
            title = result["title"].title()
            duration_min = "Live Track"
            stream_name = f"live_{result['vidid']}"
            thumbnail = result.get("thumb", None)
        elif streamtype == "index":
            file_path = result
            title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
            duration_min = "00:00"
            stream_name = "index_url"
            thumbnail = config.STREAM_IMG_URL

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                stream_name,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await join_call(file_path, thumbnail, video if streamtype != "index" else True)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                stream_name,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if streamtype in ["telegram", "live"]:
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=thumbnail,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{result.get('vidid', '')}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            if streamtype == "index":
                await mystic.delete()
