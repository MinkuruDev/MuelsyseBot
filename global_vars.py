import os
import discord
import firebase_admin

from dotenv import load_dotenv
from discord import app_commands
from firebase_admin import credentials, firestore

load_dotenv()
TOKEN = os.environ.get("TOKEN")
ALLOWED_ID = int(os.environ.get("ALLOWED_ID"))
RELEASE = int(os.environ.get("RELEASE"))
WORKDIR = os.environ.get("WORKDIR")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

# command server
PING_CHANNEL_ID = 1174532883420024893

BIRTHDAY_DATA_CHANNEL_ID = 1200733346515390564

# main server
MMM_SERVER_ID = 1160783653413068872

ANNOUNCEMENT_CHANNEL_ID = 1160862369438781440
FACEBOOK_CHANNEL_ID = 1167841637163089930
BIRTHDAY_ANNOUNCEMENT_CHANNEL_ID = 1200734259913166948
ANNIVERSARY_CHANNEL_ID = 1298189420415029299
LEADERBOARD_CHANNEL_ID = 1306809263309721711

BIRTHDAY_ROLE_ID = 1180309158919155722
SERVER_BOOSTER_ROLE_ID = 1166770283391242300
LEVEL_32_ROLE_ID = 1160870169694970020
FACEBOOK_NOTIFICATION_ROLE_ID = 1167712584720453642
ANNIVERSARY_ROLE_IDS = [
    1298182726503104553,
    1298186911181049856,
    1298186973281910844,
    1298187077300523039,
    1298187166790189076,
    1298187259006423040,
    1298187378162270208,
    1298187477332393985,
]

SHWM_PAGE_ID = 176226312250666
MWC_PAGE_ID = 107355032425494

SERVER_NICKNAME = "Muelsyse Clone"
RUNNED = False

# Discord client
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Firestore database
cred = credentials.Certificate(f'{WORKDIR}serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
all_birthday_ref = db.collection("Birthday").document("AllBirthday")
