import discord
import global_vars
import mdo_commands
import mbot_commands
import emoji as emoji_lib
import re

client = global_vars.client
tree = global_vars.tree

custom_roles = {} # map member_id : custom_role_id

@tree.command(
    name="ping",
    description="Test if the bot is up!!!",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def ping_slash(interaction):
    await interaction.response.send_message(f"Pong! ({client.latency*1000}ms)")

@tree.command(
    name="birthdayof",
    description="See someone birthday (if already set)",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def birthdy_get_slash(interaction, user: discord.Member = None):
    uid = None
    if user is None:
        uid = interaction.user.id
    else:
        uid = user.id
    
    uid = str(uid)
    if uid not in mdo_commands.birthday_data:
        await interaction.response.send_message(f"<@{uid}> birthday is not set")
    else:
        dd, mm = mdo_commands.birthday_data[uid]
        await interaction.response.send_message(f"<@{uid}> birthday is: {dd}/{mm} (dd/mm format)")

@tree.command(
    name="cr_create",
    description="Create a custom role (once only)",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def create_role_slash(interaction):
    user = interaction.user
    if user.id in custom_roles:
        cr_id = custom_roles.get(user.id)
        await interaction.response.send_message(f"{user.mention} you already have your custome role: <@&{cr_id}>")
        return
    if (discord.utils.get(user.roles, id=global_vars.SERVER_BOOSTER_ROLE_ID) is None) \
        and (discord.utils.get(user.roles, id=global_vars.LEVEL_32_ROLE_ID) is None):
        await interaction.response.send_message(f"{user.mention} you don't match the requirement to create custom role")
        return
    guild = user.guild
    new_role = await guild.create_role(name=f"custome role for {user.name}")
    server_booster_role = discord.utils.get(user.guild.roles, id=global_vars.SERVER_BOOSTER_ROLE_ID)
    await new_role.edit(position=server_booster_role.position)
    await user.add_roles(new_role)
    custom_roles[user.id] = new_role.id
    await interaction.response.send_message(f"{user.mention} create custom role successfully {new_role.mention}")

@tree.command(
    name="cr_name",
    description="Change the name of your custom role",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def create_role_name_slash(interaction, role_name:str):
    user = interaction.user
    if user.id not in custom_roles:
        await interaction.response.send_message(f"{user.mention} you don't have a custom role (use **/cr_create** to create one)")
        return
    role = discord.utils.get(user.roles, id=custom_roles.get(user.id))
    await role.edit(name=role_name)
    await interaction.response.send_message(f"{user.mention} your custom role name edited successfully")

@tree.command(
    name="cr_color",
    description="Change the color of your custom role",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def role_color_slash(interaction, hex_color:str):
    user = interaction.user
    if user.id not in custom_roles:
        await interaction.response.send_message(f"{user.mention} you don't have a custom role (use **/cr_create** to create one)")
        return
    if hex_color.startswith("#"):
        hex_color = hex_color[1::]
    try:
        color = discord.Color(int(hex_color, 16))
        role = discord.utils.get(user.roles, id=custom_roles.get(user.id))
        await role.edit(colour=color)
        await interaction.response.send_message(f"{user.mention} your custom role color edited successfully")
    except ValueError:
        await interaction.response.send_message(f"{user.mention} invalid hex color")

@tree.command(
    name="cr_icon",
    description="Change the icon of your custom role",
    guild=discord.Object(id=global_vars.MMM_SERVER_ID)
)
async def role_icon_slash(interaction, emoji:str):
    user = interaction.user
    if user.id not in custom_roles:
        await interaction.response.send_message(f"{user.mention} you don't have a custom role\n(use **/cr_create** to create one)")
        return
    
    if emoji in emoji_lib.EMOJI_DATA:
        role = discord.utils.get(user.roles, id=custom_roles.get(user.id))
        await role.edit(display_icon=emoji)
        await interaction.response.send_message(f"{user.mention} your custom role icon edited successfully")
        return
    
    if emoji.startswith("<a:"):
        await interaction.response.send_message(f"{user.mention} invalid emoji, please use a STATIC emoji\n(You are using animated emoji)")
        return

    if not re.match(r"<:(\w+):(\d+)>", emoji):
        await interaction.response.send_message(f"{user.mention} invalid emoji")
        return
    
    parts = emoji.split(":")
    eid = int(parts[2][:-1])
    e = discord.utils.get(user.guild.emojis, id=eid)
    if e is None:
        await interaction.response.send_message(f"{user.mention} invalid emoji, please use emoji from THIS SERVER")
        return

    if e.animated:
        await interaction.response.send_message(f"{user.mention} invalid emoji, please use a STATIC emoji\n(You are using animated emoji)")
        return
    
    role = discord.utils.get(user.roles, id=custom_roles.get(user.id))
    icon = await e.read()
    await role.edit(display_icon=icon)
    await interaction.response.send_message(f"{user.mention} your custom role icon edited successfully")
