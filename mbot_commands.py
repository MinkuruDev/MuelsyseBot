import global_vars
import mdo_commands
import pytz
import json

from datetime import datetime

pending_birthday = {}

# Load the command info from the JSON file
with open(global_vars.WORKDIR + 'command_info_mbot.json', 'r') as f:
    COMMAND_INFO = json.load(f)

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
        help_content = "Use **mbot help [command]** for detail.\nAvailable commands:\n"
        for cmd, info in COMMAND_INFO.items():
            help_content += f"\n**mbot {cmd}**: {info['description']}\n"
    
    await message.channel.send(help_content)

async def birthday_set_command(client, message, flag):
    args = flag.get('_args', [])
    if str(message.author.id) in mdo_commands.birthday_data:
        await message.channel.send(f"{message.author.mention} you cannot set birthday twice")
        return
    if len(args) != 2:
        await message.channel.send("Invalid argument, Syntax: ***mbot birthday_set dd mm***")
        return

    try:
        dd, mm = int(args[0]), int(args[1])
    except ValueError:
        dd, mm = 0, 0

    if not exist_date(dd, mm):
        await message.channel.send("Invalid Date")
        return

    pending_birthday[message.author.id] = (dd, mm)
    await message.channel.send(f"""{message.author.mention}
        Birthday will set to ***Day: {dd}, Month: {mm}***
        send ***mbot birthday_confirm*** to confirm your birthday.
        Once birthdays are confirmed, it cannot be set again.
        send ***mbot birthday_cancel*** to cancel
    """)

async def birthday_set_confirm(client, message, flag):
    user_id = message.author.id
    if user_id not in pending_birthday:
        await message.channel.send(f"{message.author.mention} You don't have anything to confirm. Use  ***mbot birthday_set dd mm*** to set your birthday.")
        return

    birthday_info_channel = client.get_channel(global_vars.BIRTHDAY_DATA_CHANNEL_ID)

    # Extract the pending birthday information
    dd, mm = pending_birthday.pop(user_id)

    # Send the birthday information to the birthday_info_channel
    await birthday_info_channel.send(f"{user_id} {dd} {mm}")

    # Set mdo_commands.birthday_data of uid
    str_id = str(user_id)
    mdo_commands.birthday_data[str_id] = [dd, mm]
    global_vars.all_birthday_ref.update({str_id: [dd, mm]})
    await message.channel.send(f"{message.author.mention} Birthday confirmed!")

    current_time_utc7 = datetime.now(pytz.timezone('Asia/Bangkok'))
    if (dd, mm) == (current_time_utc7.day, current_time_utc7.month):
        await mdo_commands.assign_birthday(client, user_id)

async def birthday_set_cancel(client, message, flag):
    if message.author.id not in pending_birthday:
        await message.channel.send(f"{message.author.mention} You don't have any pending birthday setting to cancel.")
        return

    # Remove the pending birthday information
    pending_birthday.pop(message.author.id)

    await message.channel.send(f"{message.author.mention} Birthday setting canceled. Use ***mbot birthday_set dd mm*** to set your birthday.")

MBOT_COMMAND_MAP = {
    'birthday_set': birthday_set_command,
    'birthday_confirm': birthday_set_confirm,
    'birthday_cancel': birthday_set_cancel,
    'help': help_command
}
