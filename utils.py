import discord
import global_vars
import re
import datetime
import pytz

from datetime import datetime, timedelta, timezone
from typing import Tuple

def get_number_from_nick(guild: discord.Guild, nick: str) -> int:
    if not re.match(rf"^{global_vars.SERVER_NICKNAME}( \d+)?$", nick):
        return None

    if nick == global_vars.SERVER_NICKNAME:
        return None

    parts = nick.split()
    return int(parts[-1])


def is_valid_nickname(guild: discord.Guild, member: discord.Member, nick: str) -> Tuple[bool, str]:
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

def parse_duration(duration_str: str) -> int:
    """
    Parse a duration string into seconds.
    Format: 1d2h30m15s (1 day, 2 hours, 30 minutes, 15 seconds)
    :param duration_str: The duration string to parse.
    """
    total_seconds = 0
    for time_match in re.finditer(r'(?P<value>\d+)(?P<unit>[dhms])', duration_str):
        value, unit = time_match.groups()
        if unit == 'd':
            total_seconds += int(value) * 86400  # 1 day = 86400 seconds
        elif unit == 'h':
            total_seconds += int(value) * 3600   # 1 hour = 3600 seconds
        elif unit == 'm':
            total_seconds += int(value) * 60
        elif unit == 's':
            total_seconds += int(value)

    return total_seconds 

def parse_to_unix_utc7(time_str):
    """
    Parses a datetime string in the format dd/mm/yyyy-hh:mm:ss (assumed in UTC+7)
    and converts it to Unix time (UTC-based).

    Args:
        time_str (str): A string in the format 'dd/mm/yyyy-hh:mm:ss'.

    Returns:
        int: Unix timestamp (seconds since epoch, UTC).
    """
    # Parse the input time (naive datetime)
    local_dt = datetime.strptime(time_str, '%H:%M:%S-%d/%m/%Y')

    # Set timezone to UTC+7
    utc7 = timezone(timedelta(hours=7))
    aware_local_dt = local_dt.replace(tzinfo=utc7)

    # Convert to UTC
    utc_dt = aware_local_dt.astimezone(timezone.utc)

    # Convert to Unix time
    unix_time = int(utc_dt.timestamp())
    return unix_time

def current_time_utc7() -> datetime:
    return datetime.now(pytz.timezone('Asia/Bangkok'))

def epoch_to(time_str: str) -> int:
    """
    Caculate the epoch delta from now to the given time string.
    The time string should be in the format dd/mm/yyyy-hh:mm:ss (assumed in UTC+7).

    Args:
        time_str (str): A string in the format 'dd/mm/yyyy-hh:mm:ss'.

    Returns:
        int: seconds until the given time from now.
    """
    return parse_to_unix_utc7(time_str) - int(current_time_utc7().timestamp())

def get_channel(channel) -> discord.TextChannel:
    """Get a channel from a string <#ID> or ID."""
    if isinstance(channel, int):
        return global_vars.client.get_channel(channel)
    # channel can be in format of <#123456789012345678> or 123456789012345678
    channel_id = int(channel[2:-1]) if channel.startswith("<#") and channel.endswith(">") else int(channel)
    return global_vars.client.get_channel(channel_id)

def get_member(guild: discord.Guild, member) -> discord.Member:
    # member can be in format of <@123456789012345678> or 123456789012345678
    member_id = int(member[2:-1]) if member.startswith("<@") and member.endswith(">") else int(member)
    return guild.get_member(member_id)


def exist_date(d, m):
    if d > 31 or d < 1:
        return False
    if m > 12 or m < 1:
        return False
    if m == 2 and d > 29:
        return False
    if m in [4, 6, 9, 11] and d > 30:
        return False
    return True

async def send_long_message(channel: discord.TextChannel, message: str):
    """
    Sends a long message to a Discord text channel, splitting at newline boundaries
    if it exceeds the 2000-character limit. Handles plain triple-backtick code blocks (```).
    """
    max_length = 2000

    # Check if the message starts and ends with plain triple backticks
    in_code_block = message.startswith("```") and message.endswith("```")

    code_header = "```\n" if in_code_block else ""
    code_footer = "```" if in_code_block else ""

    if in_code_block:
        message = message[4:-3]  # Strip the initial ```\n and trailing ```

    def chunk_message(msg_body):
        chunks = []
        limit = max_length - len(code_header) - len(code_footer)
        while len(msg_body) > limit:
            split_at = msg_body.rfind('\n', 0, limit)
            if split_at == -1:
                split_at = limit
            chunks.append(msg_body[:split_at])
            msg_body = msg_body[split_at:]
        chunks.append(msg_body)
        return chunks

    parts = chunk_message(message)

    for part in parts:
        content = f"{code_header}{part}{code_footer}" if in_code_block else part
        await channel.send(content)
