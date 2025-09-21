import asyncio
from typing import Union

from AviaxMusic.misc import db
from config import autoclean, time_to_seconds


async def put_queue(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    user_id,
    stream,
    forceplay: Union[bool, str] = None,
):
    """Insert a track into queue instantly without delay"""
    title = title.title()
    try:
        duration_in_seconds = time_to_seconds(duration) - 3
    except:
        duration_in_seconds = 0

    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "user_id": user_id,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
    }

    # Direct insertion for forceplay
    if forceplay:
        db.setdefault(chat_id, []).insert(0, put)
    else:
        db.setdefault(chat_id, []).append(put)

    # Keep track for auto-clean
    autoclean.append(file)


async def put_queue_index(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    stream,
    forceplay: Union[bool, str] = None,
):
    """Insert index/URL stream instantly, skip heavy duration checks"""
    put = {
        "title": title,
        "dur": duration or "ᴜʀʟ sᴛʀᴇᴀᴍ",
        "streamtype": stream,
        "by": user,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": 0,
        "played": 0,
    }

    if forceplay:
        db.setdefault(chat_id, []).insert(0, put)
    else:
        db.setdefault(chat_id, []).append(put)

    autoclean.append(file)
