import os
import discord

from dotenv import load_dotenv
from discord import app_commands

load_dotenv()
TOKEN = os.getenv("TOKEN")
ALLOWED_ID = int(os.getenv("ALLOWED_ID"))
RELEASE = int(os.getenv("RELEASE"))
WORKDIR = os.getenv("WORKDIR")

# command server
PING_CHANNEL_ID = 1174532883420024893

BIRTHDAY_DATA_CHANNEL_ID = 1200733346515390564

# main server
MMM_SERVER_ID = 1160783653413068872

ANNOUNCEMENT_CHANNEL_ID = 1160862369438781440
FACEBOOK_CHANNEL_ID = 1167841637163089930
BIRTHDAY_ANNOUNCEMENT_CHANNEL_ID = 1200734259913166948

BIRTHDAY_ROLE_ID = 1180309158919155722

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
