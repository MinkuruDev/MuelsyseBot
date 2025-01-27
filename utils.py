import discord
import global_vars
import re

def get_number_from_nick(guild: discord.Guild, nick: str) -> int:
    if not re.match(rf"^{global_vars.SERVER_NICKNAME}( \d+)?$", nick):
        return None

    if nick == global_vars.SERVER_NICKNAME:
        return None

    parts = nick.split()
    return int(parts[-1])

def is_valid_nickname(guild: discord.Guild, member: discord.Member, nick: str) -> (bool, str):
    # Ensure the event is for the correct guild
    if guild.id != global_vars.MMM_SERVER_ID:
        return (True, "")

    pattern = rf"^{global_vars.SERVER_NICKNAME}( \d+)?$"
    if not re.match(pattern, nick):
        return (False, "Nickname must be in the format: Muelsyse Clone [number]")

    # If there's no number, it's valid
    if nick == global_vars.SERVER_NICKNAME:
        return (True, "")
    
    parts = nick.split()
    number = int(parts[-1])
    # if the number greater than server member count x 2, it's invalid
    if number > guild.member_count * 2:
        return (False, f"Number must be less than {guild.member_count * 2}")

    # if number is 0, check for owner permission
    if number == 0:
        is_owner = guild.owner_id == member.id
        return (is_owner, "Number 0 is reserved for server owner")

    # if the number is smaller than 10, check for manage_server permission
    is_staff = member.guild_permissions.manage_guild
    if number < 10:
        return (is_staff, "Number 1-9 is reserved for staff")

    # if the number is smaller than 100, check for vip
    if number < 100:
        return (is_vip(guild, member) or is_staff, "Number 10-99 is reserved for VIP (Booster, Level 32, Top 1 Leaderboard once), and staff") 

    return (True, "")

def is_vip(guild: discord.Guild, member: discord.Member):
    booster_role = guild.get_role(global_vars.SERVER_BOOSTER_ROLE_ID)
    level_32_role = guild.get_role(global_vars.LEVEL_32_ROLE_ID)
    top_1_leaderboard_role = guild.get_role(global_vars.TOP1_LEADERBOARD_ONCE_ROLE_ID)
    
    return booster_role in member.roles \
        or level_32_role in member.roles \
        or top_1_leaderboard_role in member.roles
