import discord
import os
import json
import re

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

load_dotenv()
TOKEN = os.getenv("TOKEN")
ALLOWED_ID = int(os.getenv("ALLOWED_ID"))

# Load the command info from the JSON file
with open('command_info.json', 'r') as f:
    COMMAND_INFO = json.load(f)

client = discord.Client(intents=intents)


async def help_command(message, flags):
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

async def send_command(message, flags):
    target_channel_id = int(flags.get('--channel-id', message.channel.id))
    target_channel = client.get_channel(target_channel_id)

    if "--md-file" in flags:
        file_name = f"./mdo/{flags['--md-file']}.md"
        try:
            with open(file_name, 'r', encoding="utf-8") as file:
                content = file.read()
                await target_channel.send(content)
        except FileNotFoundError:
            await message.channel.send(f"File {file_name} not found.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
    elif "--image" in flags:
        image_path = f"./mdo/{flags['--image']}"
        try:
            await target_channel.send(file=discord.File(image_path))
        except FileNotFoundError:
            await message.channel.send(f"Image {image_path} not found.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
    else:
        await target_channel.send(" ".join(flags.get('_args', [])))

async def edit_command(message, flags):
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
            file_name = f"./mdo/{md_file}.md"
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


async def timeout_command(message, flags):
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

async def facebook_command(message, flags):
    channel_id = 1167841637163089930  # Specify the target channel ID

    file_name = "./mdo/facebook.md"
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

async def announcement_command(message, flags):
    channel_id = 1160862369438781440  # Specify the target announcement channel ID

    file_name = "./mdo/announcement.md"
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

COMMAND_MAP = {
    'send': send_command,
    'help': help_command,
    'timeout': timeout_command,
    'facebook': facebook_command,
    'announcement': announcement_command,
    'edit' : edit_command
    # ... add other commands as needed
}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('mdo'):
        if message.author.id != ALLOWED_ID:
            await message.channel.send(f"<@{message.author.id}> you don't have permission to use this command.")
            return
        
        # Command handler
        command_parts = message.content.split()
        command = command_parts[1] if len(command_parts) > 1 else None

        # Flags handler
        flags = {'_args': []}
        skip_next = False
        for idx, part in enumerate(command_parts[2:]):
            if skip_next:
                skip_next = False
                continue
            if part.startswith("--"):
                if len(command_parts) > idx + 3 and not command_parts[idx + 3].startswith("--"):
                    flags[part] = command_parts[idx + 3]
                    skip_next = True
                else:
                    flags[part] = True
            else:
                flags['_args'].append(part)

        # Execute the corresponding function from the COMMAND_MAP
        if command in COMMAND_MAP:
            await COMMAND_MAP[command](message, flags)

client.run(TOKEN)
