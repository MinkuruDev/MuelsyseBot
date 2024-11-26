import re
import json
import discord
import pytz
import global_vars
import requests
import os
import random

from discord.ext import commands
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Load the command info from the JSON file
with open(global_vars.WORKDIR + 'command_info.json', 'r') as f:
    COMMAND_INFO = json.load(f)

birthday_data = {}

async def help_command(client: discord.Client, message: discord.Message, flags: dict):
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

async def send_command(client: discord.Client, message: discord.Message, flags: dict):
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

async def edit_command(client: discord.Client, message: discord.Message, flags: dict):
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

async def timeout_command(client: discord.Client, message: discord.Message, flags: dict):
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

async def facebook_command(client: discord.Client, message: discord.Message, flags: dict):
    channel_id = global_vars.FACEBOOK_CHANNEL_ID  if global_vars.RELEASE == 1 else 898119095143260203
    url = "https://graph.facebook.com"

    try:
        params = {
            "limit": "1",
            "access_token": global_vars.FB_ACCESS_TOKEN
        }
        resp = requests.get(f"{url}/MuelsyseClone/feed", params)
        obj = json.loads(resp.text)
        post_id = obj.get("data")[0].get("id")

        params = {
            "fields": "permalink_url",
            "access_token": global_vars.FB_ACCESS_TOKEN
        }

        resp = requests.get(f"{url}/{post_id}", params)
        obj = json.loads(resp.text)
        post_url = obj.get("permalink_url")

        args = flags.get('_args', [])
        scopes = f"<@&{global_vars.FACEBOOK_NOTIFICATION_ROLE_ID}>"
        if len(args) > 0:
            if args[0] == "everyone":
                scopes = "@everyone Sorry for the ping but this is important"
            else:
                for some_id in args:
                    scopes += f"<@{some_id}>"
        
        noti_channel = client.get_channel(channel_id)
        msg = f"{scopes}\nMuelsyse's water clone just posted !!!\n{post_url}"

        await noti_channel.send(msg)

    except Exception as e:
        await message.channel.send(f"An error occurred: {e}")

async def announcement_command(client: discord.Client, message: discord.Message, flags: dict):
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

async def edit_nickname_command(client: discord.Client, message: discord.Message, flags: dict):
    guild_id = flags.get("--guild-id", global_vars.MMM_SERVER_ID)
    guild = client.get_guild(int(guild_id))
    args = flags.get("_args", [])
    if len(args) > 0:
        global_vars.SERVER_NICKNAME = " ".join(args)
    nick = global_vars.SERVER_NICKNAME

    if guild:
        members = guild.members
        owner_id = guild.owner.id
        for member in members:
            if member.bot or member.id == owner_id:
                continue
            if member.nick != nick:
                print(f"{member.name}: {member.nick} --> {nick}")
                await member.edit(nick=nick)
    else:
        print('Guild not found.')

async def birthday_command(client: discord.Client, message: discord.Message, flags: dict):
    birthday_info_channel = client.get_channel(global_vars.BIRTHDAY_DATA_CHANNEL_ID)
    guild = client.get_guild(global_vars.MMM_SERVER_ID)

    global birthday_data
    birthday_data = global_vars.all_birthday_ref.get().to_dict()
    # print(birthday_data)

    # Get current time in UTC+7
    current_time_utc7 = datetime.now(pytz.timezone('Asia/Bangkok'))

    # Check birthday roles and update accordingly
    for member in guild.members:
        # Check if the member has the birthday role
        has_birthday_role = discord.utils.get(member.roles, id=global_vars.BIRTHDAY_ROLE_ID) is not None

        str_id = str(member.id)
        if str_id in birthday_data:
            member_birthday = birthday_data[str_id]

            if has_birthday_role and member_birthday != [current_time_utc7.day, current_time_utc7.month]:
                # Remove birthday role if member has it but today is not their birthday
                await member.remove_roles(discord.Object(global_vars.BIRTHDAY_ROLE_ID))
            elif not has_birthday_role and member_birthday == [current_time_utc7.day, current_time_utc7.month]:
                await assign_birthday(client, member.id, current_time_utc7)

async def anniversary_command(client: discord.Client, message: discord.Message, flags: dict):
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    announcement_channel = client.get_channel(global_vars.ANNIVERSARY_CHANNEL_ID)
    ANNIVERSARY_ROLE_IDS = global_vars.ANNIVERSARY_ROLE_IDS
    current_time_utc7 = datetime.now(pytz.timezone('Asia/Bangkok'))
    
    for member in guild.members:
        if member.bot:  # Skip bots
            continue
        
        # Calculate how many years they've been on the server
        membership_duration = (current_time_utc7 - member.joined_at).days // 365
        if membership_duration < 1 or membership_duration > len(ANNIVERSARY_ROLE_IDS):
            continue  # Skip if the member hasn't reached their 1st anniversary or exceeds the available roles
        
        role_id = ANNIVERSARY_ROLE_IDS[membership_duration - 1]
        anniversary_role = guild.get_role(role_id)

        # Check if the member already has the role
        if discord.utils.get(member.roles, id=role_id) is None:
            # Assign the role
            await member.add_roles(anniversary_role)
            
            # Send a message to the announcement channel
            await announcement_channel.send(
                f":tada: Chúc mừng {member.mention} đã trở thành Water Clone trong vòng {membership_duration} năm :tada:"
                # "test :v"
            )

async def leaderboard_command(client: discord.Client, message: discord.Message, flags: dict):
    args = flags.get("_args", [])
    if len(args) < 2:
        await message.channel.send("Usage: `mdo leaderboard <MONTH> <YEAR>`")
        return

    try:
        month = int(args[0])
        year = int(args[1])
    except ValueError:
        await message.channel.send("Please enter valid numerical values for month and year.")
        return

    leaderboard_channel = client.get_channel(global_vars.LEADERBOARD_CHANNEL_ID)
    current_time_utc7 = datetime.now(pytz.timezone('Asia/Bangkok'))
    guild = client.get_guild(global_vars.MMM_SERVER_ID)

    # Get the category named "spam bot"
    category = discord.utils.get(guild.categories, name="spam bot")
    if category is None:
        await message.channel.send("Category 'spam bot' not found.")
        return
    
    bot_channels = []  # Assuming bot channels are stored here
    for channel in category.channels:
        # if isinstance(channel, discord.TextChannel) and channel.id not in bot_channels:
        bot_channels.append(channel.id)

    # Set date range for the specified month and year
    start_date = datetime(year, month, 1, tzinfo=pytz.timezone('Asia/Bangkok'))
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=pytz.timezone('Asia/Bangkok'))
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=pytz.timezone('Asia/Bangkok'))

    # Dictionary to store message counts per user
    msg_count = defaultdict(int)

    messagable_channels = list(guild.text_channels) + \
        list(guild.threads)
        # [channel for channel in guild.channels if isinstance(channel, discord.ForumChannel)] + \
    # Iterate through each non-bot channel in the category
    for channel in messagable_channels:
        # Skip channels that are in the bot_channels list
        if channel.id in bot_channels or not channel.permissions_for(guild.default_role).read_messages:
            continue
        
        await message.channel.send(f"checking: <#{channel.id}>")
        # Get messages within the specified month and year
        limit = 50 if global_vars.RELEASE == 0 else None
        async for msg in channel.history(after=start_date, before=end_date, limit=limit):
            if not msg.author.bot:  # Skip bot messages
                msg_count[msg.author.id] += 1

    # Sort and get the top 10 users by message count
    top_users = sorted(msg_count.items(), key=lambda x: x[1], reverse=True)[:10]

    # Format leaderboard message
    leaderboard = "🏆 **Bảng xếp hạng số tin nhắn đã gửi trong tháng {}/{}** 🏆\n".format(month, year)
    leaderboard += "*(Thống kê không tính tin nhắn được gửi trong kênh bot)*\n"
    for i, (user_id, count) in enumerate(top_users):
        user = guild.get_member(user_id)
        username = user.name if user else f"Unknown User {user_id}"
        leaderboard += f"{i + 1}. <@{user_id}> ({escape_markdown(username)}) - {count} tin nhắn\n"

    if global_vars.RELEASE == 0:
        await message.channel.send(leaderboard)
    else:
        # Send leaderboard to leaderboard channel
        await leaderboard_channel.send(leaderboard)

async def fix_missing_command(client: discord.Client, message: discord.Message, flags: dict):
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    if not guild:
        await message.channel.send("Guild not found")
        return

    for member in guild.members:
        if member.bot:
            continue
        # Ensure member has all roles in `MUST_HAVE_ROLE_IDS`
        for role_id in global_vars.MUST_HAVE_ROLE_IDS:
            role = guild.get_role(role_id)
            if role and role not in member.roles:
                try:
                    await member.add_roles(role, reason="Missing required role.")
                except discord.Forbidden:
                    await message.channel.send(f"Permission denied to modify roles for {member.name}.")
                except discord.HTTPException as e:
                    await message.channel.send(f"Error adding role to {member.name}: {e}")

        # Handle `OPTIONAL_ROLE_IDS`
        for a_id, b_id in global_vars.OPTIONAL_ROLE_IDS:
            role_a = guild.get_role(a_id)
            role_b = guild.get_role(b_id)
            
            if not role_a or not role_b:
                continue  # Skip if roles do not exist

            has_a = role_a in member.roles
            has_b = role_b in member.roles

            if not has_a and not has_b:
                # Member has neither role, give `role_a`
                try:
                    await member.add_roles(role_a, reason="Adding missing optional role A.")
                except discord.Forbidden:
                    await message.channel.send(f"Permission denied to add role A for {member.name}.")
                except discord.HTTPException as e:
                    await message.channel.send(f"Error adding role A to {member.name}: {e}")
            elif has_a and has_b:
                # Member has both roles, remove `role_a` and keep `role_b`
                try:
                    await member.remove_roles(role_a, reason="Conflict resolution: keeping role B.")
                except discord.Forbidden:
                    await message.channel.send(f"Permission denied to remove role A from {member.name}.")
                except discord.HTTPException as e:
                    await message.channel.send(f"Error removing role A from {member.name}: {e}")


def escape_markdown(text):
    # Escape Markdown special characters: *, _, ~, and `
    return re.sub(r"([*_~`])", r"\\\1", text)

async def assign_birthday(client: discord.Client, uid: int, current_time_utc7):
    # Add birthday role and announce if member has birthday today but doesn't have the role
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    member = await guild.fetch_member(uid)
    if not member:
        print(f"{uid} not in guild")
        return
    birthday_announcement_channel = client.get_channel(global_vars.BIRTHDAY_ANNOUNCEMENT_CHANNEL_ID)
    role = guild.get_role(global_vars.BIRTHDAY_ROLE_ID)
    await member.add_roles(role)

    file_name = random.choice(os.listdir(f"{global_vars.WORKDIR}mdo/birthday"))
    file_path = f"{global_vars.WORKDIR}mdo/birthday/{file_name}"
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            content = file.read()
            kw_args = {
                "member_count": guild.member_count,
                "member": f"<@{uid}>",
                "day": current_time_utc7.day,
                "month": current_time_utc7.month,
            }
            msg = content.format(**kw_args)
            await birthday_announcement_channel.send(msg) 
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

async def delete_recent_message_command(client: discord.Client, message: discord.Message, flags: dict):
    recent_messages = []
    args = flags.get("_args", [])
    lim = int(flags.get("--limit", 20))
    if len(args) < 2:
        await message.channel.send("Invalid agruments")
        return
    uid, num_del = int(args[0]), int(args[1])
    member = await message.guild.fetch_member(uid)
    if not member:
        await message.channel.send("Member not found.")
        return
    original_channel = message.channel

    # Iterate over all channels in the guild
    for channel in message.guild.channels:
        if not isinstance(channel, discord.TextChannel):  # Check if it's a text channel
            continue
        permissions = channel.permissions_for(member)
        if not permissions.send_messages:
            continue
        # Fetching the member's message history in the channel
        async for message in channel.history(limit=lim):
            if message.author.id == uid:
                # Add the message to the list
                recent_messages.append(message)

    # Sort the list of messages by time sent
    recent_messages.sort(key=lambda msg: msg.created_at, reverse=True)

    # Delete the specified number of recent messages
    messages_deleted = 0
    for message in recent_messages:
        await message.delete()
        messages_deleted += 1
        if messages_deleted >= num_del:
            break

    await original_channel.send(f"Deleted {messages_deleted} recent messages from {member.name}")

COMMAND_MAP = {
    'send': send_command,
    'help': help_command,
    'timeout': timeout_command,
    'facebook': facebook_command,
    'announcement': announcement_command,
    'edit' : edit_command,
    'nickname': edit_nickname_command,
    'birthday': birthday_command,
    'anniversary': anniversary_command,
    'leaderboard': leaderboard_command,
    'fix': fix_missing_command,
    'prune': delete_recent_message_command,
    # ... add other commands as needed
}
