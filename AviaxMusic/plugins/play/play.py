from pyrogram.types import InlineKeyboardButton

# Queue control markup (for Now Playing message)
def aq_markup(language: str, chat_id: int):
    return [
        [
            InlineKeyboardButton("⏯ Pause/Resume", callback_data=f"pause_resume|{chat_id}"),
            InlineKeyboardButton("⏭ Skip", callback_data=f"skip|{chat_id}")
        ],
        [
            InlineKeyboardButton("⏹ Stop", callback_data=f"stop|{chat_id}"),
            InlineKeyboardButton("📃 Queue", callback_data=f"queue|{chat_id}")
        ]
    ]


# Track markup (for single YouTube/Spotify/Apple search result)
def track_markup(_, vidid: str, user_id: int, cplay: str, fplay: str):
    return [
        [
            InlineKeyboardButton(
                text="▶️ Play",
                callback_data=f"MusicStream {vidid}|{user_id}|a|{cplay}|{fplay}"
            ),
            InlineKeyboardButton(
                text="▶️ Video",
                callback_data=f"MusicStream {vidid}|{user_id}|v|{cplay}|{fplay}"
            ),
        ]
    ]


# Playlist markup (YouTube, Spotify, Apple Music playlists)
def playlist_markup(_, playlist_id: str, user_id: int, ptype: str, cplay: str, fplay: str):
    return [
        [
            InlineKeyboardButton(
                text="🎶 Play Playlist",
                callback_data=f"AviaxPlaylists {playlist_id}|{user_id}|{ptype}|a|{cplay}|{fplay}"
            ),
            InlineKeyboardButton(
                text="🎬 Video Playlist",
                callback_data=f"AviaxPlaylists {playlist_id}|{user_id}|{ptype}|v|{cplay}|{fplay}"
            ),
        ]
    ]


# Livestream markup (for streams with no duration, like radio)
def livestream_markup(_, vidid: str, user_id: int, mode: str, cplay: str, fplay: str):
    return [
        [
            InlineKeyboardButton(
                text="📡 Start Live Stream",
                callback_data=f"MusicStream {vidid}|{user_id}|{mode}|{cplay}|{fplay}"
            )
        ]
    ]


# Slider markup (for search results navigation)
def slider_markup(_, vidid: str, user_id: int, query: str, query_type: int, cplay: str, fplay: str):
    return [
        [
            InlineKeyboardButton("⬅️ Previous", callback_data=f"slider B|{query_type}|{query}|{user_id}|{cplay}|{fplay}"),
            InlineKeyboardButton("➡️ Next", callback_data=f"slider F|{query_type}|{query}|{user_id}|{cplay}|{fplay}")
        ],
        [
            InlineKeyboardButton(
                text="▶️ Play",
                callback_data=f"MusicStream {vidid}|{user_id}|a|{cplay}|{fplay}"
            ),
            InlineKeyboardButton(
                text="▶️ Video",
                callback_data=f"MusicStream {vidid}|{user_id}|v|{cplay}|{fplay}"
            ),
        ]
    ]


# Bot playlist markup (when no query provided)
def botplaylist_markup(_):
    return [
        [InlineKeyboardButton("⭐ Trending", callback_data="bot_playlist trending")],
        [InlineKeyboardButton("🔥 Popular", callback_data="bot_playlist popular")],
        [InlineKeyboardButton("🎵 Latest", callback_data="bot_playlist latest")]
    ]
