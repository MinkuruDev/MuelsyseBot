import discord
import global_vars
import mdo_commands
import mbot_commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

COMMAND_MAP = mdo_commands.COMMAND_MAP
MBOT_COMMAND_MAP = mbot_commands.MBOT_COMMAND_MAP

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    if global_vars.RELEASE != 0:
        await mdo_commands.edit_nickname_command(client, None, None)
        await mdo_commands.birthday_command(client, None, None)

@client.event
async def on_member_join(member):
    if member.guild.id == global_vars.MMM_SERVER_ID:
        await member.edit(nick="Muelsyse Clone")

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    if client.user.mentioned_in(message):
        pinged_channel = client.get_channel(global_vars.PING_CHANNEL_ID)
        if pinged_channel:
            ping_message = f"<@{global_vars.ALLOWED_ID}> Muelsyse got memtioned at {message.jump_url}"
            await pinged_channel.send(ping_message)

    is_mdo = message.content.startswith('mdo')
    if is_mdo or message.content.startswith('mbot'):
        if message.author.id != global_vars.ALLOWED_ID and is_mdo:
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
        if is_mdo:
            # Execute the corresponding function from the COMMAND_MAP
            if command in COMMAND_MAP:
                await COMMAND_MAP[command](client, message, flags)
                print("Executed: mdo", command)
        else:
            if command in MBOT_COMMAND_MAP:
                await MBOT_COMMAND_MAP[command](client, message, flags)
                print("Executed: mbot", command)

client.run(global_vars.TOKEN)
