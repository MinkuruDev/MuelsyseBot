import global_vars
import mdo_parser
import utils
import requests
import json
import discord_log
import io
import mdo_commands

import re
import discord
import pytz
import os
import random
import slash_commands
import asyncio
import time

from discord.ext import commands
from datetime import datetime, timedelta, timezone
from collections import defaultdict

birthday_data = {}
client = global_vars.client
logger : discord_log.DiscordLogger

async def help_command(args):
    if args.cmd:
        help_message = mdo_parser.get_help_command(args.cmd)
        logger.DEBUG(f"Help command requested for: {args.cmd}")
    else:
        help_message = mdo_parser.get_help_command()
        logger.DEBUG("General help command requested")
    
    return help_message

async def send_command(args):
    if args.image:
        channel = utils.get_channel(args.channel)
        if args.image.startswith("http://") or args.image.startswith("https://"):
            logger.VERBOSE(f"Fetching content from URL: {args.file}")
            try:
                response = requests.get(args.image)
                response.raise_for_status()  # Raise an error for bad responses
                await channel.send(file=discord.File(io.BytesIO(response.content), filename="image.png"))
                args.quiet = True  # Set quiet to True if sending an image from URL
                logger.VERBOSE("Image sent from url successfully. Setting quiet to True.")
            except requests.RequestException as e:
                logger.ERROR(f"Error fetching content from URL: {e}")
                return f"Error fetching content from URL: {e}"
        else:
            logger.VERBOSE(f"Sending image from local path: {args.image}")
            try:
                await channel.send(file=discord.File(args.image))
                args.quiet = True  # Set quiet to True if sending a local image
                logger.VERBOSE("Image sent from local path successfully. Setting quiet to True.")
            except discord.HTTPException as e:
                logger.ERROR(f"Error sending image: {e}")
                return f"Error sending image: {e}"
            
    # return the context or content in the file
    if args.file:
        with open(args.file, 'r') as f:
            content = f.read()
            logger.VERBOSE(f"Read content from file: {args.file}")
    else:
        content = " ".join(args.context)
        logger.VERBOSE(f"Constructed content from context: {content}")
    
    return content

async def edit_command(args):
    channel = utils.get_channel(args.message_channel)
    if not channel:
        logger.ERROR(f"Channel {args.message_channel} not found")
        return f"Channel {args.message_channel} not found"
    message = await channel.fetch_message(args.message_id)
    if not message:
        logger.ERROR(f"Message {args.message_id} not found in channel {args.message_channel}")
        return f"Message {args.message_id} not found in channel {args.message_channel}"
    if args.file:
        with open(args.file, 'r') as f:
            logger.VERBOSE(f"Reading content from file: {args.file}")
            content = f.read()
    else:
        content = " ".join(args.context)
        logger.VERBOSE(f"Constructed content from context: {content}")
    await message.edit(content=content)
    return f"Message {args.message_id} edited in channel {channel.mention}"

async def announcement_command(args):
    if not args.debug:
        args.channel = global_vars.ANNOUNCEMENT_CHANNEL_ID
    with open("announcement.md", 'r') as f:
        logger.DEBUG("Reading content from announcement.md")
        content = f.read()
    return content

async def facebook_command(args):
    url = "https://graph.facebook.com"
    try:
        params = {
            "limit": "1",
            "access_token": global_vars.FB_ACCESS_TOKEN
        }
        resp = requests.get(f"{url}/MuelsyseClone/feed", params)
        logger.VERBOSE(f"response from Facebook API: {resp.text}")
        obj = json.loads(resp.text)
        post_id = obj.get("data")[0].get("id")

        params = {
            "fields": "permalink_url",
            "access_token": global_vars.FB_ACCESS_TOKEN
        }

        resp = requests.get(f"{url}/{post_id}", params)
        logger.VERBOSE(f"response from Facebook API: {resp.text}")
        obj = json.loads(resp.text)
        post_url = obj.get("permalink_url")
        # embed link, change 'facebook' from post_url to 'facebed'
        embed_url = post_url.replace("facebook", "facebed")
    except Exception as e:
        logger.ERROR(f"Error fetching Facebook post: {e}")
        return f"An error occurred: {e}"
    
    if not args.debug:
        args.channel = global_vars.FACEBOOK_CHANNEL_ID
        # push the facebook role id to the front of mentions
    args.mention.insert(0, f"&{global_vars.FACEBOOK_ROLE_ID}")

    return f"Muelsyse's water clone vừa mới đăng bài !!!\n{embed_url}\nNếu link embed không hoạt động, sử dụng link này:\n{post_url}"

async def timeout_command(args):
    guild = client.get_guild(args.guild)
    member = utils.get_member(guild, args.member)
    if not member:
        return f"Member {args.member} not found"
    logger.VERBOSE(f"Timeout command for member: {member} in guild: {guild.name} (ID: {guild.id})")
    
    seconds = utils.parse_duration(args.duration)
    logger.VERBOSE(f"Parsed duration '{args.duration}' into seconds: {seconds}")
    if not seconds:
        return "Invalid duration format. Use e.g., 1h, 30m, 15s, 1d12h30m6s"
    
    reason = " ".join(args.reason) if args.reason else "No reason provided"
    
    try:
        timeout_duration = timedelta(seconds=seconds)
        await member.timeout(timeout_duration, reason=reason)
        logger.VERBOSE(f"Timed out member {member.name} for {seconds} seconds with reason: {reason}")
        return f"{member.mention} has been timed out for {args.duration}\nReason: {reason}"
    except Exception as e:
        logger.ERROR(f"Error timing out member {member.name}: {e}")
        return f"An error occurred while timing out the member: {e}"

async def nickname_command(args):
    if args.guild != global_vars.MMM_SERVER_ID:
        logger.ERROR("Guild ID does not match the MMM server ID.")
        return "This command can only be used in the MMM server."
    
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    nick = global_vars.SERVER_NICKNAME

    if guild:
        members = guild.members
        owner_id = guild.owner.id
        for member in members:
            if member.bot or member.id == owner_id:
                continue
            valid, reason = utils.is_valid_nickname(guild, member, member.nick or "")
            if not valid:

                logger.INFO(f"{member.name}: {member.nick} --> {nick}")
                logger.INFO(f"Reason: {reason}")

                try:
                    await member.edit(nick=nick, reason=reason)
                except discord.Forbidden:
                    logger.ERROR(f"Permission denied to change nickname for {member.name}.")
                except discord.HTTPException as e:
                    logger.ERROR(f"Failed to change nickname for {member.name}: {e}")
        
        await list_nick_numbers()
        logger.DEBUG(slash_commands.nick_numbers.__str__())
        return "command executed successfully."
    else:
        logger.WARNING("Guild not found. Please ensure the bot is connected to the MMM server.")
        return "Guild not found. Please ensure the bot is connected to the MMM server."


async def list_nick_numbers():
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    for member in guild.members:
        if member.nick is None or member.bot:
            continue
        number = utils.get_number_from_nick(guild, member.nick)
        if number is not None:
            slash_commands.nick_numbers[member.id] = number
            slash_commands.nick_numbers[number] = member.id
            logger.VERBOSE(f"Added nickname number mapping: {discord.utils.escape_markdown(member.name)} ({member.id}) -> {number}")

async def anniversary_command(args):
    if args.guild != global_vars.MMM_SERVER_ID:
        logger.ERROR("Guild ID does not match the MMM server ID.")
        return "This command can only be used in the MMM server."
    
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
            logger.VERBOSE(f"Assigned {anniversary_role.name} to {member.name} for {membership_duration} year(s) of membership.")

            # Send a message to the announcement channel
            await announcement_channel.send(
                f":tada: Chúc mừng {member.mention} đã trở thành Water Clone trong vòng {membership_duration} năm :tada:"
                # "test :v"
            )
    
    return f"Anniversary command executed successfully. Checked {len(guild.members)} members for anniversaries."

async def assign_birthday(client: discord.Client, uid: int, current_time_utc7):
    # Add birthday role and announce if member has birthday today but doesn't have the role
    logger.VERBOSE(f"Assigning birthday role to user {uid} for birthday on {current_time_utc7.day}/{current_time_utc7.month}")
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
    logger.VERBOSE(f"Selected birthday announcement file: {file_path}")
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
        logger.ERROR(f"File {file_path} not found.")
    except Exception as e:
        logger.ERROR(f"An error occurred when assign birthday: {e}")

async def birthday_command(args):
    if args.guild != global_vars.MMM_SERVER_ID:
        logger.ERROR("Guild ID does not match the MMM server ID.")
        return "This command can only be used in the MMM server."
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
                logger.VERBOSE(f"Removed birthday role from {member.name} ({member.id}) as today is not their birthday.")
            elif not has_birthday_role and member_birthday == [current_time_utc7.day, current_time_utc7.month]:
                await assign_birthday(client, member.id, current_time_utc7)
                logger.VERBOSE(f"Assigned birthday role to {member.name} ({member.id}) as today is their birthday.")

    return f"Birthday command executed successfully. Checked {len(guild.members)} members for birthdays."

def split_into_equal_timestamps(start_date, end_date, num_splits=10):
    """Generates a list of equal time ranges between start_date and end_date."""
    total_duration = end_date - start_date
    split_duration = total_duration / num_splits
    
    for i in range(num_splits):
        current = start_date + i * split_duration
        next_timestamp = start_date + (i + 1) * split_duration
        yield current, next_timestamp

async def process_messages_in_channel(channel, start_date, end_date, limit=None):
    """Processes messages for a specific channel within the given time range and returns local counts."""
    local_count = defaultdict(int)
    local_total = 0

    # limit = None # debug Super active month
    async for msg in channel.history(after=start_date, before=end_date, limit=limit):
        if not msg.author.bot:
            local_count[msg.author.id] += 1
            local_total += 1

    return local_count, local_total, channel.id

async def indexing_leaderboard_command(args):
    if args.guild != global_vars.MMM_SERVER_ID:
        logger.ERROR("Guild ID does not match the MMM server ID.")
        return "This command can only be used in the MMM server."

    year = args.year
    month = args.month
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    sam_diff = args.sam_diff
    sam_total = 50_000 + sam_diff * 10_000
    sam_top10 = 2000 + sam_diff * 500

    # List of category names not to count messages from
    category_names = ["spam bot", "Doro777"]

    # Find all matching categories
    categories = [cat for cat in guild.categories if cat.name in category_names]

    bot_channels = []
    if not categories:
        logger.WARNING("None of the Bot categories were found.")
    else:
        # Collect all channel IDs from the matched categories
        bot_channels = [channel.id for category in categories for channel in category.channels]
    
    start_date = datetime(year, month, 1, tzinfo=pytz.timezone('Asia/Bangkok'))
    end_date = datetime(year + 1, 1, 1, tzinfo=pytz.timezone('Asia/Bangkok')) if month == 12 else datetime(year, month + 1, 1, tzinfo=pytz.timezone('Asia/Bangkok'))
    
    msg_count = defaultdict(int)
    channel_msg_count = defaultdict(int)
    total_messages = 0
    limit = 50 if args.debug else None  # Set limit to 50 for debugging, otherwise None

    very_active_channels = [1160783654168035381, 1398657031300190258]
    messagable_channels = list(guild.text_channels) + list(guild.threads)
    
    tasks = []
    for channel in messagable_channels:
        if channel.id in bot_channels or channel.id in very_active_channels or not channel.permissions_for(guild.default_role).send_messages:
            continue
        
        logger.INFO(f"Checking: <#{channel.id}>")
        tasks.append(process_messages_in_channel(channel, start_date, end_date, limit=limit))
    
    for active_channel_id in very_active_channels:
        channel = client.get_channel(active_channel_id)
        if channel is None:
            continue
        
        logger.INFO(f"Checking: <#{active_channel_id}>")
        for day_start, day_end in split_into_equal_timestamps(start_date, end_date, 2):
            tasks.append(process_messages_in_channel(channel, day_start, day_end, limit=limit))
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.INFO(f"Elapsed time: {elapsed_time:.2f} seconds")
    time_str = f"{utils.current_time_utc7().strftime('%H:%M:%S %d/%m/%Y')}"

    for local_count, local_total, channel_id in results:
        for user_id, count in local_count.items():
            msg_count[f"{user_id}"] += count
        total_messages += local_total
        channel_msg_count[f"{channel_id}"] += local_total
    
    top_users = sorted(msg_count.items(), key=lambda x: x[1], reverse=True)[:10]
    is_sam = total_messages >= sam_total or (top_users[-1][1] if top_users else 0) >= sam_top10

    results = {
        "by_user": dict(msg_count),
        "by_channel": dict(channel_msg_count),
        "total": total_messages,
        "total_user": len(msg_count),
        "total_channel": len(channel_msg_count),
        "sam_diff": sam_diff,
        "is_sam": is_sam,
        "last_update": time_str
    }

    # Save the results to the database
    # print(results)
    global_vars.db.collection("Leaderboard").document(f"{year}{month:02d}").set(results)

    return f"Indexing completed for {month}/{year}."

async def leaderboard_command(args):
    if args.guild != global_vars.MMM_SERVER_ID:
        logger.ERROR("Guild ID does not match the MMM server ID.")
        return "This command can only be used in the MMM server."
    if not args.debug:
        args.channel = global_vars.LEADERBOARD_CHANNEL_ID

    args.after = True
    args.mention.insert(0, f"&{global_vars.SERVER_UPDATE_NOTIFICATION_ROLE_ID}")

    year = args.year
    month = args.month
    guild = client.get_guild(global_vars.MMM_SERVER_ID)

    # Fetch the leaderboard data from the database
    doc = global_vars.db.collection("Leaderboard").document(f"{year}{month:02d}").get()

    if not doc.exists:
        logger.WARNING(f"Leaderboard data for {month}/{year} not found in the database. Start indexing...")
        await indexing_leaderboard_command(args)
        doc = global_vars.db.collection("Leaderboard").document(f"{year}{month:02d}").get()
    
    data = doc.to_dict()
    msg_count = data.get("by_user", {})
    total_messages = data.get("total", 0)
    updated_at = data.get("last_update", "Unknown time")
    user_count = data.get("total_user", 0)
    channel_count = data.get("total_channel", 0)
    sam_diff = data.get("sam_diff", 0)
    sam_total = 50_000 + sam_diff * 10_000
    sam_top10 = 2000 + sam_diff * 500

    extended = sorted(msg_count.items(), key=lambda x: x[1], reverse=True)[:20]
    top_users = extended[:10]
    is_sam = total_messages >= sam_total or (top_users[-1][1] if top_users else 0) >= sam_top10

    near_top_1 = set()
    joint_top_1 = set()

    if top_users:
        top_1_msg = top_users[0][1]
        top_10_msg = top_users[9][1] if len(top_users) >= 10 else 0

        for i, (user_id, count) in enumerate(top_users[1:], start=2):
            if count / top_1_msg >= 0.99:  # 99% of top 1 messages
                near_top_1.add(user_id)

            if count == top_1_msg:  # Equal to top 1
                joint_top_1.add(user_id)

        # If the leaderboard qualifies for "Đồng top 1" condition (top 10 has > 1000 messages)
        if top_10_msg >= 1000:
            joint_top_1.update(near_top_1)

        # If SAM conditions are met, apply to ranks #4 - #10 using #3 as reference
        if is_sam and len(top_users) >= 3:
            top_3_msg = top_users[2][1]  # #3 messages count
            near_top_1.clear()
            joint_top_1.clear()

            for i, (user_id, count) in enumerate(top_users[3:], start=4):
                if count / top_3_msg >= 0.99:  # 99% of top 3 messages
                    near_top_1.add(user_id)

                if count == top_3_msg:  # Equal to top 3
                    joint_top_1.add(user_id)

            if top_10_msg >= 1000:
                joint_top_1.update(near_top_1)

    leaderboard = f"🏆 **Bảng xếp hạng số tin nhắn đã gửi trong tháng {month}/{year}** 🏆\n"
    leaderboard += "*(Thống kê không tính tin nhắn được gửi trong kênh bot)*\n"
    leaderboard += f"Độ khó của Super Active Month: **{sam_diff}**\n"
    leaderboard += f"*({sam_total} tổng tin nhắn **hoặc** người đứng top 10 đạt {sam_top10} tin nhắn)*\n\n"
    for i, (user_id, count) in enumerate(top_users, start=1):
        user = guild.get_member(int(user_id))
        username = user.name if user else f"Unknown User {user_id}"
        leaderboard += f"{i}. <@{user_id}> ({discord.utils.escape_markdown(username)}) - {count} tin nhắn"
        if user_id in joint_top_1:
            leaderboard += " (Đồng top 1)\n"
        elif user_id in near_top_1:
            leaderboard += " (Gần top 1)\n"
        else:
            leaderboard += "\n"
    leaderboard += f"Tổng số lượng tin nhắn (Kể cả ngoài bảng xếp hạng): **{total_messages}**\n"
    
    if is_sam:
        leaderboard += "\n:tada: **Hiển thị bảng xếp hạng đến #20 cho Super Active Month!** :tada:\n"
        for i, (user_id, count) in enumerate(extended[10:], start=11):
            user = guild.get_member(int(user_id))
            username = user.name if user else f"Unknown User {user_id}"
            leaderboard += f"{i}. <@{user_id}> ({discord.utils.escape_markdown(username)}) - {count} tin nhắn\n"
    
    leaderboard += f"\nBảng xếp hạng được cập nhật vào lúc **{updated_at}**\n"
    leaderboard += f"Tổng số member nhắn tin trong tháng: **{user_count}**\n" + \
        f"Tổng số channel/threads/post được đếm: **{channel_count}**\n" + \
        f"Nếu bạn không trong bảng xếp hạng, có thể kiểm tra bằng lệnh `/ranking` tại <#1200793753259098242>\n"

    return leaderboard

async def fix_command(args):
    if args.guild != global_vars.MMM_SERVER_ID:
        logger.ERROR("Guild ID does not match the MMM server ID.")
        return "This command can only be used in the MMM server."
    guild = client.get_guild(global_vars.MMM_SERVER_ID)

    for member in guild.members:
        if member.bot:
            continue
        # Ensure member has all roles in `MUST_HAVE_ROLE_IDS`
        for role_id in global_vars.MUST_HAVE_ROLE_IDS:
            role = guild.get_role(role_id)
            if role and role not in member.roles:
                try:
                    await member.add_roles(role, reason="Missing required role.")
                    logger.VERBOSE(f"Added role {role.name} to {member.name} ({member.id})")
                except discord.Forbidden:
                    logger.ERROR(f"Permission denied to modify roles for {member.name}.")
                except discord.HTTPException as e:
                    logger.ERROR(f"Error adding role to {member.name}: {e}")

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
                    logger.VERBOSE(f"Added role {role_a.name} to {member.name} ({member.id})")
                except discord.Forbidden:
                    logger.ERROR(f"Permission denied to add role A for {member.name}.")
                except discord.HTTPException as e:
                    logger.ERROR(f"Error adding role A to {member.name}: {e}")
            elif has_a and has_b:
                # Member has both roles, remove `role_a` and keep `role_b`
                try:
                    await member.remove_roles(role_a, reason="Conflict resolution: keeping role B.")
                    logger.VERBOSE(f"Removed role {role_a.name} from {member.name} ({member.id})")
                except discord.Forbidden:
                    logger.ERROR(f"Permission denied to remove role A from {member.name}.")
                except discord.HTTPException as e:
                    logger.ERROR(f"Error removing role A from {member.name}: {e}")

    return "Fix command executed successfully. All members have been checked and roles updated as necessary."

async def prune_command(args):
    recent_messages = []

    guild = client.get_guild(args.guild)
    member = utils.get_member(guild, args.member)
    uid = member.id
    num_del = args.number

    if not member:
        logger.ERROR(f"Member {args.member} not found in guild {guild.name} (ID: {guild.id})")
        return

    # Function to fetch messages from a single channel
    async def fetch_member_messages(channel):
        messages = []
        if not isinstance(channel, discord.TextChannel):
            return messages
        permissions = channel.permissions_for(member)
        if not permissions.send_messages:
            return messages
        async for message in channel.history(limit=args.limit):
            if message.author.id == uid:
                messages.append(message)
        return messages

    # Create and gather tasks for each eligible channel
    tasks = [fetch_member_messages(channel) for channel in guild.channels]
    results = await asyncio.gather(*tasks)

    # Flatten the list of lists into a single list of messages
    for msg_list in results:
        recent_messages.extend(msg_list)

    # Sort messages by created_at (most recent first)
    recent_messages.sort(key=lambda msg: msg.created_at, reverse=True)

    # Delete up to the specified number of messages
    messages_deleted = 0
    for message in recent_messages:
        await message.delete()
        messages_deleted += 1
        if messages_deleted >= num_del:
            break

    logger.VERBOSE(f"Deleted {messages_deleted} messages from {member.name} ({uid}) in guild {guild.name} (ID: {guild.id})")
    return f"Deleted {messages_deleted} recent messages from {member.name}"

async def set_birthday_command(args):
    if args.guild != global_vars.MMM_SERVER_ID:
        logger.ERROR("Guild ID does not match the MMM server ID.")
        return "This command can only be used in the MMM server."
    
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    member = utils.get_member(guild, args.member)
    user_id = member.id
    dd = args.day
    mm = args.month

    if not utils.exist_date(dd, mm):
        logger.WARNING(f"Invalid date provided: {dd}/{mm} for user {user_id}.")
        return "Invalid Date"

    birthday_info_channel = client.get_channel(global_vars.BIRTHDAY_DATA_CHANNEL_ID)

    # Send the birthday information to the birthday_info_channel
    await birthday_info_channel.send(f"{user_id} {dd} {mm}")

    # Set mdo_commands.birthday_data of uid
    str_id = str(user_id)
    birthday_data[str_id] = [dd, mm]
    global_vars.all_birthday_ref.update({str_id: [dd, mm]})

    current_time_utc7 = datetime.now(pytz.timezone('Asia/Bangkok'))
    if (dd, mm) == (current_time_utc7.day, current_time_utc7.month):
        await assign_birthday(client, user_id, current_time_utc7)

    logger.VERBOSE(f"Set birthday for user {user_id} to {dd}/{mm}.")
    return f"Birthday for user <@{user_id}> set to {dd}/{mm}."

COMMAND_MAP = {
    "help": help_command,
    "send": send_command,
    "edit": edit_command,
    "nickname": nickname_command,
    "announcement": announcement_command,
    "facebook": facebook_command,
    "timeout": timeout_command,
    "anniversary": anniversary_command,
    "birthday": birthday_command,
    "leaderboard": leaderboard_command,
    "fix": fix_command,
    "prune": prune_command,
    "set-birthday": set_birthday_command,
    "index-lb": indexing_leaderboard_command,
}
