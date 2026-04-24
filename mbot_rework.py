import asyncio
import discord
import mbot_parser
import utils
import mdo_rework
import slash_commands
import global_vars
import random
import mdo_parser
import mdo_rework

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

async def timeout_with_rate(member: discord.Member, rate: float, reason: str = None) -> dict[str, float] | None:
    duration = 3
    _369_rate = 0.36
    if random.random() * 100 < rate:
        duration = 36 
        if rate >= 100.0:
            _369_rate = 3.6 + (rate - 100.0) * 0.36
        if random.random() * 100 < _369_rate:
            duration = 369
    elif random.random() * 100 < 50:
        duration = 6
    
    try:
        muzzle_result = timedelta(seconds=duration)
        await member.timeout(muzzle_result, reason=reason)
    except Exception as e:
        print(f"Failed to timeout <@{member.id}>: {str(e)}")
        return None
    
    result = {
        'duration': duration,
        '369_rate': _369_rate,
    }
    if rate >= 100.0:
        result['36_rate'] = 100.0 - _369_rate
        result['3_rate'] = 0.0
    else:
        result['36_rate'] = rate - _369_rate
        result['3_rate'] = (100.0 - rate) / 2
    return result

def format_output(success = False, reverse = False, mod_action = False, rate = 0.0, target_id = None, **kwargs) -> str:
    if not success:
        res = '**[Muzzle failed]**\n'
        res += f'**Success chance**: {rate:.2f}%'
        return res

    res = '**[Muzzle reverse]**' if reverse else '**[Muzzle success]**'
    if mod_action:
        res += ' (Mod action)'
    res += '\n'

    res += f'<@{target_id}> has been timed out for {kwargs.get('duration', 0)} seconds\n'
    res += f'**Reason**: {kwargs.get('reason', 'No reason provided')}\n'
    res += f'**Timeout chance**: {rate:.2f}%\n' if not reverse else f'**Reverse change**: {rate:.2f}%\n'
    res += f'**Duration rarity**:\n'
    res += f'- 369s: {kwargs.get('369_rate', 0.0):.2f}%\n'
    res += f'- 36s: {kwargs.get('36_rate', 0.0):.2f}%\n'
    res += f'- 6s: {kwargs.get('3_rate', 0.0):.2f}%\n'
    res += f'- 3s: {kwargs.get('3_rate', 0.0):.2f}%\n'

    return res

async def muzzled(args):
    reason = " ".join(args.reason) if args.reason else "No reason provided"
    guild = client.get_guild(args.guild)
    target = utils.get_member(guild, str(args.target))
    commander = utils.get_member(guild, str(args.member))

    if target is None:
        return f"Target: {args.target} not found"

    # Check if target has timeout permmision
    if target.guild_permissions.moderate_members:
        # reverse effect
        muzzle_result = await timeout_with_rate(commander, 190.0, reason="You Gotta Move reverse effect")
        if muzzle_result is not None:
            return format_output(True, True, False, 190.0, commander.id, reason="Are you trying to muzzled a mod?", **muzzle_result)

    # check if commander have you gotta move role
    if global_vars.YOU_GOTTA_MOVE_ROLE_ID in [role.id for role in commander.roles]:
        # reverse effect
        muzzle_result = await timeout_with_rate(commander, 140.0, reason="You Gotta Move reverse effect")
        if muzzle_result is not None:
            return format_output(True, True, False, 140.0, commander.id, reason="You are the target for muzzled, not the commander", **muzzle_result)
    
    # Check if target not have You Gotta Move role
    if not global_vars.YOU_GOTTA_MOVE_ROLE_ID in [role.id for role in target.roles]:
        return f"<@{target.id}> can't be muzzled."

    # get 12 recent messages from channel
    channel = client.get_channel(args.channel)
    counter = 0
    async for msg in channel.history(limit=12):
        if msg.author.id == client.user.id and msg.content.startswith("**[Muzzle"):
            return f"Muzzle command is on cooldown in this channel. Send {12 - counter} more messages to use again."
        counter += 1

    rate = 0
    rr = 3.6
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
                rr += 3.6
        if msg.author.id == commander.id:
            rate += 3.6

    if not msg_flag:
        rate /= 3.6

    # check if commander has timeout permission
    if commander.guild_permissions.moderate_members:
        muzzle_result = await timeout_with_rate(target, 100.0+rate, reason)
        if muzzle_result is not None:
            return format_output(True, False, True, 100.0+rate, target.id, reason=reason, **muzzle_result)

    # check if timeout success:
    if random.random() * 100 < rate:
        muzzle_result = await timeout_with_rate(target, rate, reason)
        if muzzle_result is not None:
            return format_output(True, False, False, rate, target.id, reason=reason, **muzzle_result)
    elif random.random() * 100 < rr:
        # reverse effect
        muzzle_result = await timeout_with_rate(commander, rate/3.6, reason="You Gotta Move reverse effect")
        if muzzle_result is not None:
            return format_output(True, True, False, (1-rate/100)*rr, commander.id, reason="UNO Reverse", **muzzle_result)

    return format_output(False, False, False, rate, target.id)

async def deathmatch(args):
    if args.round % 2 == 0 or args.round < 1 or args.round > 9:
        return "Round must be an odd number between 1 and 9"
    seconds = utils.parse_duration(args.duration)
    if seconds is None:
        return "Invalid duration format. Use formats like '60m', '1d', '12h', etc."
    if seconds > 3 * 24 * 3600:
        return "Duration must be less than or equal to 3 days"
    target = utils.get_member(client.get_guild(args.guild), str(args.target))
    if target is None:
        return f"Target: {args.target} not found"
    commander = utils.get_member(client.get_guild(args.guild), str(args.member))
    if commander is None:
        return f"Commander: {args.member} not found"
    if global_vars.YOU_GOTTA_MOVE_ROLE_ID in [role.id for role in target.roles]:
        return f"<@{target.id}> can't be challenged to deathmatch. They are already in You Gotta Move role"
    if global_vars.YOU_GOTTA_MOVE_ROLE_ID in [role.id for role in commander.roles]:
        return f"<@{commander.id}> You can't challenge to deathmatch. You are already in You Gotta Move role"
    if target.guild_permissions.moderate_members:
        return f"<@{target.id}> is a moderator and can't be challenged to deathmatch"

    channel = client.get_channel(args.channel)
    msg = f"# DEATHMATCH BATTLE\n"
    msg += f"<@{commander.id}> vs <@{target.id}>\n"
    msg += f"Format: Best of {args.round} rounds\n"
    await channel.send(msg)
    await asyncio.sleep(3)

    commander_score = 0
    target_score = 0
    max_score = args.round // 2 + 1

    for round in range(1, args.round + 1):
        extra_rate = 10.0 - 20.0 * random.random()
        rate = 50.0 + extra_rate
        msg = f"## Round {round}\n"
        msg += f"Round win rate:\n"
        msg += f"- **{commander.name}**: {rate:.2f}%\n"
        msg += f"- **{target.name}**: {100.0 - rate:.2f}%\n"
        msg += f"The fate chooses..."
        await channel.send(msg)

        if random.random() * 100 < rate:
            commander_score += 1
            winner = commander
        else:
            target_score += 1
            winner = target
        
        await asyncio.sleep(3)
        msg = f"**{winner.name}** wins this round!\n"
        msg += f"Score: **{commander.name}**: {commander_score} - {target_score} **{target.name}**\n"
        await channel.send(msg)
        await asyncio.sleep(3)

        if commander_score == max_score or target_score == max_score:
            break
    
    if commander_score > target_score:
        winner = commander
        loser = target
    else:
        winner = target
        loser = commander
    
    a = mdo_parser.parse_str_command(f"mdo give-role {loser.id} {global_vars.YOU_GOTTA_MOVE_ROLE_ID} --duration {args.duration}")
    await mdo_rework.give_role_command(a)
    return f"**{winner.mention} wins the deathmatch!**\n<@{loser.id}> has been given You Gotta Move role for {args.duration}."

async def russian_roulette(args):
    duration = utils.parse_duration(args.duration)
    if duration is None:
        return f"Invalid duration: '{args.duration}'"
    if duration <= 0:
        return f"Duration must be greater than 0"
    if duration > 69:
        return f"Duration must be less than or equal to 69 seconds"

    guild = client.get_guild(args.guild)
    commander = utils.get_member(guild, str(args.member))
    if commander is None:
        return "Commander not found"
        
    if len(args.targets) > 5:
        return "You can only challenge up to 5 other members"
        
    targets = []
    for t in args.targets:
        m = utils.get_member(guild, t)
        if m is None:
            return f"Target {t} not found"
        if m in targets or m == commander:
            return "Duplicate participants are not allowed"
        targets.append(m)
        
    has_ygm = global_vars.YOU_GOTTA_MOVE_ROLE_ID in [role.id for role in commander.roles]
    
    if has_ygm:
        if len(targets) != 1:
            return "You have 'You gotta move' role, so you can only challenge exactly 1 other member in this game."
        participants = [commander, targets[0], commander, commander, commander, commander]
    else:
        participants = [commander] + targets
        
    channel = client.get_channel(args.channel)
    msg = "# RUSSIAN ROULETTE\nGame participants:\n"
    for idx, p in enumerate(participants):
        msg += f"**{idx + 1}**. <@{p.id}>\n"
        
    await channel.send(msg)
    await asyncio.sleep(2)
    
    bullet_chamber = random.randint(1, 6)
    current_chamber = random.randint(1, 6)
    
    await channel.send("The bullet is loaded. The cylinder is spun. Let the game begin!")
    await asyncio.sleep(2)
    
    turn = 0
    while True:
        current_player = participants[turn % len(participants)]
        msg = f"## Turn {turn + 1}\n"
        msg += f"Current chamber: **{current_chamber}**\n"
        msg += f"**{current_player.name}** places the gun to their head and pulls the trigger...\n"
        await channel.send(msg)
        await asyncio.sleep(2)
        
        if current_chamber == bullet_chamber:
            final_msg = f"## BANG!\n"
            
            if current_player.guild_permissions.moderate_members:
                final_msg += f"\n<@{current_player.id}> is a moderator and is immune to the timeout!"
            else:
                final_duration = duration
                if global_vars.YOU_GOTTA_MOVE_ROLE_ID in [r.id for r in current_player.roles]:
                    final_duration = int(duration * 3.6)
                try:
                    await current_player.timeout(timedelta(seconds=final_duration), reason="Shot in Russian Roulette")
                    final_msg += f"\n<@{current_player.id}> has been timed out for {final_duration} seconds."
                except Exception as e:
                    final_msg += f"\nFailed to timeout <@{current_player.id}>: {str(e)}"
            return final_msg
        else:
            msg_click = f"*click*. They pass the gun."
            await channel.send(msg_click)
            await asyncio.sleep(2)
            
            turn += 1
            current_chamber += 1
            if current_chamber > 6:
                current_chamber = 1


MBOT_COMMAND_MAP = {
    'help': help_command,
    'set-birthday': birthday_set_command,
    'check-birthday': check_birthday_command,
    'set-number': set_number_command,
    'ranking': ranking_command,
    'muzzled': muzzled,
    'deathmatch': deathmatch,
    'russian-roulette': russian_roulette,
}
