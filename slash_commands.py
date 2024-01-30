import discord
import global_vars
import mdo_commands
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

@tree.command(
    name="birthdayof",
    description="See someone birthday (if already set)",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def birthdy_get_slash(interaction, user: discord.Member = None):
    uid = None
    if user is None:
        uid = interaction.user.id
    else:
        uid = user.id
    
    if uid not in mdo_commands.birthday_data:
        await interaction.response.send_message(f"<@{uid}> birthday is not set")
    else:
        dd, mm = mdo_commands.birthday_data[uid]
        await interaction.response.send_message(f"<@{uid}> birthday is: {dd}/{mm} (dd/mm format)")
