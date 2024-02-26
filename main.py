import asyncio
import discord
import global_vars
import mdo_commands
import mbot_commands
import slash_commands
import daily

client = global_vars.client
tree = slash_commands.tree

COMMAND_MAP = mdo_commands.COMMAND_MAP
MBOT_COMMAND_MAP = mbot_commands.MBOT_COMMAND_MAP

async def do_daily():
    await mdo_commands.edit_nickname_command(client, None, None)
    await mdo_commands.birthday_command(client, None, None)
    print("Executed daily task at:", daily.get_utc_plus_7_time())

async def list_custom_roles():
    guild = client.get_guild(global_vars.MMM_SERVER_ID)
    roles = guild.roles[::-1] # Reverse the roles list to iterate from top to bottom
    custom_role = False
    for role in roles:
        if role.id == global_vars.BIRTHDAY_ROLE_ID:
            custom_role = True
            continue
        if not custom_role:
            continue
        if role.id == global_vars.SERVER_BOOSTER_ROLE_ID:
            break
        if len(role.members) == 0:
            continue
        mem = role.members[0]
        slash_commands.custom_roles[mem.id] = role.id

async def start_up():
    await list_custom_roles()

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=global_vars.MMM_SERVER_ID))
    print(f'We have logged in as {client.user}')
    asyncio.create_task(daily.daily(do_daily))
    await start_up()
    if global_vars.RELEASE != 0:
        print('Running in RELEASE mode')
        await do_daily()
    else:
        print("Running in DEBUG mode")

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
