import discord
import global_vars
import mdo_commands
import mbot_commands
import mdo_rework
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
    if uid not in mdo_rework.birthday_data:
        await interaction.response.send_message(f"<@{uid}> birthday is not set")
    else:
        dd, mm = mdo_rework.birthday_data[uid]
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

@tree.command(
    name="ranking",
    description="See your leaderboard ranking in specified month and year",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
@app_commands.describe(
    month = "Month to see ranking (1-12). Leave empty for last month",
    year = "Year to see ranking. Leave empty to auto detect based on month",
)
async def ranking_slash(interaction: discord.Interaction, month: int = None, year: int = None):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    now = utils.current_time_utc7()

    if month is None:
        if year is not None:
            await interaction.followup.send(f"Month must be specified first if year is specified")
            return
        
        month = now.month - 1
        year = now.year
        if month == 0:
            month = 12
            year -= 1
    
    if month < 1 or month > 12:
        await interaction.followup.send(f"Month must be between 1 and 12")
        return

    if year is None:
        year = now.year
        if month >= now.month:
            year -= 1

    if year < 2023 or year > now.year:
        await interaction.followup.send(f"Year must be between 2023 and {now.year}")
        return

    lb = global_vars.db.collection("Leaderboard").document(f"{year}{month:02d}")
    lb_data = lb.get().to_dict()

    if lb_data is None:
        await interaction.followup.send(f"No leaderboard data for {month}/{year}")
        return
    
    by_user = lb_data.get("by_user", {})
    total_messages = lb_data.get("total", 0)
    total_users = lb_data.get("total_user", 0)
    last_update = lb_data.get("last_update", None)

    count = by_user.get(uid, 0)
    if count == 0:
        await interaction.followup.send(f"You have no messages in {month}/{year}")
        return
    
    ranking = 1
    for user_id, msg_count in by_user.items():
        if user_id == uid:
            continue
        if msg_count > count:
            ranking += 1
    
    response = f"# Ranking in {month}/{year}\n"
    response += f"*User:* <@{uid}>\n"
    response += f"*Ranking:* **#{ranking}**/{total_users}\n"
    response += f"*Number of messages:* **{count}**/{total_messages} ({count/total_messages*100:.2f}%)\n"
    response += f"*Data updated in:* **{last_update}**\n"
    await interaction.followup.send(response)
