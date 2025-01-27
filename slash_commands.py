import discord
import global_vars
import mdo_commands
import mbot_commands
import utils

from discord import app_commands

client = global_vars.client
tree = global_vars.tree

nick_numbers = {} # map member_id : number, and number : member_id

@tree.command(
    name="ping",
    description="Test if the bot is up!!!",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! ({client.latency*1000}ms)")

@tree.command(
    name="birthdayof",
    description="See someone birthday (if already set)",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
@app_commands.describe(
    user = "User to see birthday, leave empty to see your own birthday",
)
async def birthdy_get_slash(interaction: discord.Interaction, user: discord.Member = None):
    uid = None
    if user is None:
        uid = interaction.user.id
    else:
        uid = user.id
    
    uid = str(uid)
    if uid not in mdo_commands.birthday_data:
        await interaction.response.send_message(f"<@{uid}> birthday is not set")
    else:
        dd, mm = mdo_commands.birthday_data[uid]
        await interaction.response.send_message(f"<@{uid}> birthday is: {dd}/{mm} (dd/mm format)")

@tree.command(
    name="set_number",
    description="Set your nickname number",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
@app_commands.describe(
    number = "Your nickname number, leave empty to delete your number",
)
async def set_number_slash(interaction: discord.Interaction, number: int = None):
    uid = interaction.user.id
    user = interaction.user
    if number is None:
        if uid in nick_numbers:
            await user.edit(nick=global_vars.SERVER_NICKNAME)
            await interaction.response.send_message(f"Deleted your nickname number")
        else:
            await interaction.response.send_message(f"You don't have a nickname number to delete")
        return
    
    if number in nick_numbers:
        await interaction.response.send_message(f"Number {number} is already taken")
        return

    valid, reason = utils.is_valid_nickname(interaction.guild, user, f"{global_vars.SERVER_NICKNAME} {number}")
    
    if not valid:
        await interaction.response.send_message(f"Invalid nickname number: {reason}")
        return

    await user.edit(nick=f"{global_vars.SERVER_NICKNAME} {number}")
    await interaction.response.send_message(f"Set your nickname number to {number}")
