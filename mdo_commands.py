import re
import json
import discord
from discord.ext import commands
import pytz
import global_vars

from datetime import datetime, timedelta, timezone

# Load the command info from the JSON file
with open(global_vars.WORKDIR + 'command_info.json', 'r') as f:
    COMMAND_INFO = json.load(f)

birthday_data = {}

async def help_command(client, message, flags):
    command_parts = message.content.split()
    
    # If there's a specific command asked for in the help (e.g., mdo help send)
    if len(command_parts) > 2 and command_parts[2] in COMMAND_INFO:
        cmd = command_parts[2]
        info = COMMAND_INFO[cmd]
        
        help_content = f"**{info['usage']}**\n\n{info['description']}\n"
        
        if 'args' in info:
            help_content += "\n**Arguments**:\n"
            for arg, arg_desc in info['args'].items():
                help_content += f"- {arg}: {arg_desc}\n"

        if 'flags' in info:
            help_content += "\n**Flags**:\n"
            for flag, flag_desc in info['flags'].items():
                help_content += f"- {flag}: {flag_desc}\n"
                
    else:  # General help without specific command
        help_content = "Use **mdo help [command]** for detail.\nAvailable commands:\n"
        for cmd, info in COMMAND_INFO.items():
            help_content += f"\n**mdo {cmd}**: {info['description']}\n"
    
    await message.channel.send(help_content)

async def send_command(client, message, flags):
    target_channel_id = int(flags.get('--channel-id', message.channel.id))
    target_channel = client.get_channel(target_channel_id)

    if "--md-file" in flags:
        file_name = f"{global_vars.WORKDIR}mdo/{flags['--md-file']}.md"
        try:
            with open(file_name, 'r', encoding="utf-8") as file:
                content = file.read()
                await target_channel.send(content)
        except FileNotFoundError:
            await message.channel.send(f"File {file_name} not found.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
    elif "--image" in flags:
        image_path = f"{global_vars.WORKDIR}mdo/{flags['--image']}"
        try:
            await target_channel.send(file=discord.File(image_path))
        except FileNotFoundError:
            await message.channel.send(f"Image {image_path} not found.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
    else:
        await target_channel.send(" ".join(flags.get('_args', [])))

async def edit_command(client, message, flags):
    # Extract channel ID and message ID from args
    args = flags.get('_args', [])

    if len(args) < 2:
        await message.channel.send("Please provide both the channel ID and message ID.")
        return

    channel_id, msg_id = args[:2]

    try:
        # Convert channel ID and message ID to integers
        channel_id = int(channel_id)
        msg_id = int(msg_id)

        # Get the target channel from the client
        target_channel = client.get_channel(channel_id)

        if not target_channel:
            await message.channel.send("Channel not found.")
            return

        # Get the target message
        target_message = await target_channel.fetch_message(msg_id)

        if not target_message:
            await message.channel.send("Message not found.")
            return

        # Check if --MD-FILE is provided
        md_file = flags.get('--md-file')
        if md_file:
            # Read content from the Markdown file
            file_name = f"{global_vars.WORKDIR}mdo/{md_file}.md"
            with open(file_name, 'r', encoding="utf-8") as file:
                context = file.read()
        else:
            # Check if [CONTEXT] is provided
            context = ' '.join(args[2:])

        # Edit the message
        await target_message.edit(content=f"{context}".strip())
        await message.channel.send(f"Message edited successfully.")

    except ValueError:
        await message.channel.send("Invalid channel ID or message ID.")
    except FileNotFoundError:
        await message.channel.send(f"File {file_name} not found.")
    except Exception as e:
        await message.channel.send(f"An error occurred: {e}")

async def timeout_command(client, message, flags):
    args = flags.get('_args', [])

    if len(args) < 2:
        await message.channel.send("Please provide both member ID and duration.")
        return

    member_id = args[0]
    duration_str = args[1]

    # Convert duration_str to timedelta
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

    if total_seconds == 0:
        await message.channel.send("Invalid duration format. Use d, h, m, s as units. E.g., 1h30m, 5m, 90s.")
        return

    # Fetch member
    try:
        member = await message.guild.fetch_member(int(member_id))
        if not member:
            await message.channel.send("Member not found.")
            return

        # Form the timeout reason
        timeout_reason = "No reason provided"
        if len(args) > 2:
            timeout_reason = "Reason: " + " ".join(args[2:])

        # Timeout the member
        timeout_duration = timedelta(seconds=total_seconds)
        await member.timeout(timeout_duration, reason=timeout_reason)
        noti_channel_id = flags.get('--noti-channel', message.channel.id)
        noti_channel = client.get_channel(int(noti_channel_id))
        await noti_channel.send(f"{member.mention} has been timed out for {duration_str}. {timeout_reason}")

    except Exception as e:
        await message.channel.send(f"An error occurred: {e}")

async def facebook_command(client, message, flags):
    channel_id = global_vars.FACEBOOK_CHANNEL_ID  # Specify the target channel ID

    file_name = f"{global_vars.WORKDIR}mdo/facebook.md"
    try:
        with open(file_name, 'r', encoding="utf-8") as file:
            content = file.read()
            target_channel = client.get_channel(channel_id)

            if target_channel:
                await target_channel.send(content)
            else:
                await message.channel.send(f"Target channel not found.")
    except FileNotFoundError:
        await message.channel.send(f"File {file_name} not found.")
    except Exception as e:
        await message.channel.send(f"An error occurred: {e}")

async def announcement_command(client, message, flags):
    channel_id = global_vars.ANNOUNCEMENT_CHANNEL_ID  # Specify the target announcement channel ID

    file_name = f"{global_vars.WORKDIR}mdo/announcement.md"
    try:
        with open(file_name, 'r', encoding="utf-8") as file:
            content = file.read()
            target_channel = client.get_channel(channel_id)

            if target_channel:
                await target_channel.send(content)
            else:
                await message.channel.send("Announcement channel not found.")
    except FileNotFoundError:
        await message.channel.send(f"File {file_name} not found.")
    except Exception as e:
        await message.channel.send(f"An error occurred: {e}")

async def edit_nickname_command(client, message, flags):
    guild = client.get_guild(global_vars.MMM_SERVER_ID)

    if guild:
        members = guild.members
        for member in members:
            if member.bot:
                continue
            if member.nick != "Muelsyse Clone":
                print(f"{member.name}: {member.nick} --> Muelsyse Clone")
                await member.edit(nick="Muelsyse Clone")
    else:
        print('Guild not found.')

async def birthday_command(client, message, flag):
    birthday_info_channel = client.get_channel(global_vars.BIRTHDAY_DATA_CHANNEL_ID)
    guild = client.get_guild(global_vars.MMM_SERVER_ID)

    # Retrieve and parse birthday information from birthday_info_channel
    async for message in birthday_info_channel.history(limit=None):
        mem_id, day, month = map(int, message.content.split())
        # Store the birthday information in the dictionary
        birthday_data[mem_id] = (day, month)

    # Get current time in UTC+7
    current_time_utc7 = datetime.now(pytz.timezone('Asia/Bangkok'))

    # Check birthday roles and update accordingly
    for member in guild.members:
        # Check if the member has the birthday role
        has_birthday_role = discord.utils.get(member.roles, id=global_vars.BIRTHDAY_ROLE_ID) is not None

        if member.id in birthday_data:
            member_birthday = birthday_data[member.id]

            if has_birthday_role and member_birthday != (current_time_utc7.day, current_time_utc7.month):
                # Remove birthday role if member has it but today is not their birthday
                await member.remove_roles(discord.Object(global_vars.BIRTHDAY_ROLE_ID))
            elif not has_birthday_role and member_birthday == (current_time_utc7.day, current_time_utc7.month):
                await assign_birthday(client, member.id)

async def assign_birthday(client, uid):
    # Add birthday role and announce if member has birthday today but doesn't have the role
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    member = await guild.fetch_member(uid)
    if not member:
        print(f"{uid} not in guild")
        return
    birthday_announcement_channel = client.get_channel(global_vars.BIRTHDAY_ANNOUNCEMENT_CHANNEL_ID)
    role = guild.get_role(global_vars.BIRTHDAY_ROLE_ID)
    await member.add_roles(role)
    await birthday_announcement_channel.send(f"Happy Birthday, {member.mention}!")

COMMAND_MAP = {
    'send': send_command,
    'help': help_command,
    'timeout': timeout_command,
    'facebook': facebook_command,
    'announcement': announcement_command,
    'edit' : edit_command,
    'nickname': edit_nickname_command,
    'birthday': birthday_command
    # ... add other commands as needed
}
