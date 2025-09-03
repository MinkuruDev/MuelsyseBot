import mbot_parser
import utils
import mdo_rework
import slash_commands
import global_vars

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

MBOT_COMMAND_MAP = {
    'help': help_command,
    'set-birthday': birthday_set_command,
    'check-birthday': check_birthday_command,
    'set-number': set_number_command,
    'ranking': ranking_command,
}
