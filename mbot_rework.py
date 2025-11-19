import discord
import mbot_parser
import utils
import mdo_rework
import slash_commands
import global_vars
import random

from datetime import timedelta

client = global_vars.client

async def help_command(args):
    if args.cmd:
        help_message = mbot_parser.get_help_command(args.cmd)
    else:
        help_message = mbot_parser.get_help_command()
    
    return help_message

async def birthday_set_command(args):
    day = args.day
    month = args.month

    if not utils.exist_date(day, month):
        return f"```\nInvalid date: {day}/{month}\n```"
    
    uid = args.member
    str_id = str(uid)
    args.member = str_id  # convert to string for mdo_rework

    if str_id in mdo_rework.birthday_data:
        dd, mm = mdo_rework.birthday_data[str_id]
        return f"<@{str_id}> Birthday already set to {dd}/{mm}"

    return await mdo_rework.set_birthday_command(args)

async def set_number_command(args):
    uid = args.member
    guild = client.get_guild(args.guild)
    user = utils.get_member(guild, str(uid))

    if args.delete:
        if uid in slash_commands.nick_numbers:
            await user.edit(nick=global_vars.SERVER_NICKNAME)
            return "Deleted your nickname number"
        else:
            return "You don't have a nickname number to delete"
        
    number = args.number
    if number is None:
        return "You must provide a number to set"

    if number in slash_commands.nick_numbers:
        return f"Number {number} is already taken"
    
    valid, reason = utils.is_valid_nickname(user.guild, user, f"{global_vars.SERVER_NICKNAME} {number}")
    if not valid:
        return f"Invalid nickname number: {reason}"
    
    await user.edit(nick=f"{global_vars.SERVER_NICKNAME} {number}")
    return f"Set your nickname number to {number}"

async def ranking_command(args):
    month = args.month
    year = args.year
    uid = str(args.member)
    now = utils.current_time_utc7()

    if month is None:
        if year is not None:
            return "Month must be specified first if year is specified"
        
        month = now.month - 1
        year = now.year
        if month == 0:
            month = 12
            year -= 1
    
    if month < 1 or month > 12:
        return "Month must be between 1 and 12"

    if year is None:
        year = now.year
        if month >= now.month:
            year -= 1

    if year < 2023 or year > now.year:
        return f"Year must be between 2023 and {now.year}"

    lb = global_vars.db.collection("Leaderboard").document(f"{year}{month:02d}")
    lb_data = lb.get().to_dict()

    if lb_data is None:
        return f"No leaderboard data for {month}/{year}"
    
    by_user = lb_data.get("by_user", {})
    total_messages = lb_data.get("total", 0)
    total_users = lb_data.get("total_user", 0)
    last_update = lb_data.get("last_update", None)

    count = by_user.get(uid, 0)
    if count == 0:
        return f"You have no messages in {month}/{year}"
    
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
    return response

async def check_birthday_command(args):
    target = args.user

    if target is None:
        target = str(args.member)
    
    guild = client.get_guild(args.guild)
    target_id = utils.get_member(guild, target).id
    
    uid = str(target_id)
    if uid not in mdo_rework.birthday_data:
        return f"<@{uid}> birthday is not set"
    else:
        dd, mm = mdo_rework.birthday_data[uid]
        return f"<@{uid}> birthday is: {dd}/{mm} (dd/mm format)"

async def timeout_with_rate(member: discord.Member, rate: float, reason: str = None) -> int:
    duration = 3
    if random.random() * 100 < rate:
        duration = 36 
    elif random.random() * 100 < 50:
        duration = 6
    
    try:
        timeout_duration = timedelta(seconds=duration)
        await member.timeout(timeout_duration, reason=reason)
    except Exception as e:
        print(f"Failed to timeout <@{member.id}>: {str(e)}")
        return 0
    return duration

async def muzzled(args):
    you_gotta_move_role_id = 1440204182740144230
    reason = " ".join(args.reason) if args.reason else "No reason provided"
    guild = client.get_guild(args.guild)
    target = utils.get_member(guild, str(args.target))
    commander = utils.get_member(guild, str(args.member))

    if target is None:
        return f"Target: {args.target} not found"

    # check if commander have you gotta move role
    if you_gotta_move_role_id in [role.id for role in commander.roles]:
        # reverse effect
        timeout_duration = await timeout_with_rate(commander, 100.0, reason="You Gotta Move reverse effect")
        if timeout_duration > 0:
            return f"[Muzzle reverse]\n<@{commander.id}> You are the target for muzzled, not the commander!\nYou have been timed out for {timeout_duration} seconds."
    
    # Check if target not have You Gotta Move role
    if not you_gotta_move_role_id in [role.id for role in target.roles]:
        return f"<@{target.id}> is not muzzled."

    # Check if target has timeout permmision
    if target.guild_permissions.moderate_members:
        # reverse effect
        timeout_duration = await timeout_with_rate(commander, 100.0, reason="You Gotta Move reverse effect")
        if timeout_duration > 0:
            return f"[Muzzle reverse]\n<@{commander.id}> You cannot muzzle a moderator\nYou have been timed out for {timeout_duration} seconds."

    # get 12 recent messages from channel
    channel = client.get_channel(args.channel)
    if channel is None:
        return f"Channel ID {args.channel} not found in guild."
    counter = 0
    async for msg in channel.history(limit=12):
        if msg.author.id == client.user.id and msg.content.startswith("[Muzzle"):
            return f"Muzzle command is on cooldown in this channel. Send {12 - counter} more messages to use again."
        counter += 1

    rate = 3.6
    msg_flag = False
    async for msg in channel.history(limit=36):
        if msg.author.id == target.id:
            msg_flag = True
            # check if message has attachment or link
            if msg.attachments or \
                "http://" in msg.content or \
                "https://" in msg.content:
                rate += 18.0
            else:
                rate += 3.6
        if msg.author.id == commander.id:
            rate += 3.6

    if not msg_flag:
        rate /= 3.6

    # check if commander has timeout permission
    if commander.guild_permissions.moderate_members:
        timeout_duration = await timeout_with_rate(target, 100.0, reason)
        if timeout_duration > 0:
            return f"[Muzzle success]\n<@{target.id}> has been timed out for {timeout_duration} seconds.\nReason: {reason}.\n(Mod action)"

    # check if timeout success:
    if random.random() * 100 < rate:
        timeout_duration = await timeout_with_rate(target, rate, reason)
        if timeout_duration > 0:
            return f"[Muzzle success]\n<@{target.id}> has been timed out for {timeout_duration} seconds.\nReason: {reason}.\n({rate:.2f}% change to timeout and ({rate:.2f}% for 36s)"
    elif random.random() * 100 < 3.6:
        # reverse effect
        timeout_duration = await timeout_with_rate(commander, rate/3.6, reason="You Gotta Move reverse effect")
        if timeout_duration > 0:
            return f"[Muzzle reverse]\n<@{commander.id}> You have been timed out for {timeout_duration} seconds.\n({(rate * 0.036):.2f}% change to Reverse and ({(rate/3.6):.2f}% for 36s))"

    return f"[Muzzle failed], You failed to muzzle with the success change is {rate:.2f}%" 
    

MBOT_COMMAND_MAP = {
    'help': help_command,
    'set-birthday': birthday_set_command,
    'check-birthday': check_birthday_command,
    'set-number': set_number_command,
    'ranking': ranking_command,
    'muzzled': muzzled,
}
