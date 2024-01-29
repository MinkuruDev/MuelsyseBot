import discord
import global_vars
import mbot_commands

client = global_vars.client
tree = global_vars.tree

@tree.command(
    name="ping",
    description="Test if the bot is up!!!",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def ping_slash(interaction):
    await interaction.response.send_message(f"Pong! ({client.latency*1000}ms)")
