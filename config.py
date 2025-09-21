import os
import re
from dotenv import load_dotenv
from pyrogram import filters

# ✅ Load .env file
load_dotenv()

# === Required Variables ===
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Bass + Volume Boost Filter
BASS_BOOST = "bass=g=15,volume=2,equalizer=f=40:width_type=h:width=50:g=10"


if not API_ID or not API_HASH or not BOT_TOKEN:
    raise SystemExit("[ERROR] - API_ID, API_HASH, or BOT_TOKEN not set in .env file.")

# === Optional Variables with defaults or None ===
MONGO_DB_URI = os.getenv("MONGO_DB_URI", None)
DURATION_LIMIT_MIN = int(os.getenv("DURATION_LIMIT", 60))

LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = os.getenv("HEROKU_API_KEY")

API_URL = os.getenv("API_URL", 'https://api.thequickearn.xyz')
API_KEY = os.getenv("API_KEY", "30DxNexGenBotsffb036")

UPSTREAM_REPO = os.getenv("UPSTREAM_REPO", "https://github.com/ryzenop07/RyzenMusicX")
UPSTREAM_BRANCH = os.getenv("UPSTREAM_BRANCH", "master")
GIT_TOKEN = os.getenv("GIT_TOKEN", None)

SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/ryzensupport")
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/Ryzen_supportxc")

AUTO_LEAVING_ASSISTANT = os.getenv("AUTO_LEAVING_ASSISTANT", "False").lower() == "true"

PRIVACY_LINK = os.getenv("PRIVACY_LINK", "https://telegra.ph/Privacy-Policy-for-AviaxMusic-08-14")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", None)
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", None)

PLAYLIST_FETCH_LIMIT = int(os.getenv("PLAYLIST_FETCH_LIMIT", 25))

TG_AUDIO_FILESIZE_LIMIT = int(os.getenv("TG_AUDIO_FILESIZE_LIMIT", 104857600))
TG_VIDEO_FILESIZE_LIMIT = int(os.getenv("TG_VIDEO_FILESIZE_LIMIT", 2145386496))

# String sessions
STRING1 = os.getenv("STRING_SESSION", None)
STRING2 = os.getenv("STRING_SESSION2", None)
STRING3 = os.getenv("STRING_SESSION3", None)
STRING4 = os.getenv("STRING_SESSION4", None)
STRING5 = os.getenv("STRING_SESSION5", None)

# Pyrogram Filters / State Holders
BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

# Static Image URLs
START_IMG_URL = os.getenv("START_IMG_URL", "https://graph.org//file/25115719697ed91ef5672.jpg")
PING_IMG_URL = os.getenv("PING_IMG_URL", "https://graph.org//file/389a372e8ae039320ca6c.png")
PLAYLIST_IMG_URL = "https://graph.org//file/3dfcffd0c218ead96b102.png"
STATS_IMG_URL = "https://graph.org//file/99a8a9c13bb01f9ac7d98.png"
TELEGRAM_AUDIO_URL = "https://graph.org//file/2f7debf856695e0ef0607.png"
TELEGRAM_VIDEO_URL = "https://graph.org//file/2f7debf856695e0ef0607.png"
STREAM_IMG_URL = "https://te.legra.ph/file/bd995b032b6bd263e2cc9.jpg"
SOUNCLOUD_IMG_URL = "https://te.legra.ph/file/bb0ff85f2dd44070ea519.jpg"
YOUTUBE_IMG_URL = "https://graph.org//file/2f7debf856695e0ef0607.png"
SPOTIFY_ARTIST_IMG_URL = "https://te.legra.ph/file/37d163a2f75e0d3b403d6.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://te.legra.ph/file/b35fd1dfca73b950b1b05.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://te.legra.ph/file/95b3ca7993bbfaf993dcb.jpg"

# Convert MM:SS to total seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

# Duration in seconds
DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

# === URL Format Validation ===
if SUPPORT_CHANNEL and not re.match(r"^(http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - Your SUPPORT_CHANNEL url is invalid. Must start with http(s)://")

if SUPPORT_GROUP and not re.match(r"^(http|https)://", SUPPORT_GROUP):
    raise SystemExit("[ERROR] - Your SUPPORT_GROUP url is invalid. Must start with http(s)://")

