import os
import discord

from dotenv import load_dotenv
from discord import app_commands

load_dotenv()
TOKEN = os.environ.get("TOKEN")
ALLOWED_ID = int(os.environ.get("ALLOWED_ID"))
RELEASE = int(os.environ.get("RELEASE"))
WORKDIR = os.environ.get("WORKDIR")

# command server
PING_CHANNEL_ID = 1174532883420024893

BIRTHDAY_DATA_CHANNEL_ID = 1200733346515390564

# main server
MMM_SERVER_ID = 1160783653413068872

ANNOUNCEMENT_CHANNEL_ID = 1160862369438781440
FACEBOOK_CHANNEL_ID = 1167841637163089930
BIRTHDAY_ANNOUNCEMENT_CHANNEL_ID = 1200734259913166948

BIRTHDAY_ROLE_ID = 1180309158919155722
SERVER_BOOSTER_ROLE_ID = 1166770283391242300
LEVEL_32_ROLE_ID = 1160870169694970020
FACEBOOK_NOTIFICATION_ROLE_ID = 1167712584720453642

SHWM_PAGE_ID = 176226312250666
MWC_PAGE_ID = 107355032425494

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
