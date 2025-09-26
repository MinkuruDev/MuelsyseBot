import asyncio
import discord
import global_vars
import mdo_commands
import mdo_parser
import mdo_rework
import mbot_commands
import mbot_parser
import mbot_rework
import slash_commands
import daily
import utils
import re
import discord_log
import datetime
import totp

client = global_vars.client
tree = slash_commands.tree

COMMAND_MAP = mdo_commands.COMMAND_MAP
MBOT_COMMAND_MAP = mbot_commands.MBOT_COMMAND_MAP

async def do_daily():
    args = mdo_parser.parse_str_command(f"mdo nickname")
    await mdo_rework.nickname_command(args)
    args = mdo_parser.parse_str_command(f"mdo birthday")
    await mdo_rework.birthday_command(args)
    args = mdo_parser.parse_str_command(f"mdo anniversary")
    await mdo_rework.anniversary_command(args)
    previous_day = utils.current_time_utc7() - datetime.timedelta(days=1)
    mm = previous_day.month
    yyyy = previous_day.year
    args = mdo_parser.parse_str_command(f"mdo index-lb {mm} {yyyy}")
    print("Executed daily task at:", utils.current_time_utc7())
    res = await mdo_rework.indexing_leaderboard_command(args)
    print(res)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=global_vars.MMM_SERVER_ID))
    print(f'We have logged in as {client.user}')
    global_vars.logger = discord_log.DiscordLogger(
        log_channel=client.get_channel(global_vars.LOG_CHANNEL_ID)
    )
    mdo_rework.logger = global_vars.logger
    global_vars.logger.INFO(f"Logged in as {client.user.name} ({client.user.id})")
    if global_vars.RELEASE != 0:
        print('Running in RELEASE mode')
        if global_vars.RUNNED:
            return
        global_vars.RUNNED = True
        await do_daily()
        asyncio.create_task(daily.daily(do_daily))
    else:
        print("Running in DEBUG mode")
    global_vars.logger.flush()

@client.event
async def on_member_join(member: discord.Member):
    if member.guild.id == global_vars.MMM_SERVER_ID:
        await member.edit(nick=global_vars.SERVER_NICKNAME)

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # skip bot
    if before.bot:
        return
    # Ensure the event is for the correct guild
    if before.guild.id == global_vars.MMM_SERVER_ID:
        # Check if the nickname changed
        if before.nick != after.nick:
            old_nick = before.nick or before.name  # Fallback to username
            new_nick = after.nick or after.name   # Fallback to username

            if before.id in slash_commands.nick_numbers:
                num = slash_commands.nick_numbers.pop(before.id, None)
                if num is not None:
                    slash_commands.nick_numbers.pop(num, None)
            
            number = utils.get_number_from_nick(before.guild, new_nick)
            if number is not None:
                slash_commands.nick_numbers[before.id] = number
                slash_commands.nick_numbers[number] = before.id

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user or message.author.bot:
        return

    if client.user.mentioned_in(message):
        pinged_channel = client.get_channel(global_vars.PING_CHANNEL_ID)
        if pinged_channel:
            ping_message = f"<@{global_vars.ALLOWED_ID}> Muelsyse got memtioned at {message.jump_url}"
            await pinged_channel.send(ping_message)

    is_mdo = message.content.startswith('mdo')
    if not is_mdo and message.content[:4].lower() != 'mbot':
        return  # Not a command we handle
    
    if message.author.id != global_vars.ALLOWED_ID and is_mdo:
        await message.channel.send(f"<@{message.author.id}> you don't have permission to use this command.")
        return

    command_parts = message.content.split(" ")
    command = command_parts[1] if len(command_parts) > 1 else None

    if is_mdo:
        logger = global_vars.logger
        # catch the help command before parsing args
        # if the parser is get the help command, it will stop the whole process
        help_match = re.match(r"^mdo\s+([a-zA-Z0-9_-]+)\s+(?:-h|--help)\b", message.content)
        if help_match:
            help_message = mdo_parser.get_help_command(command)
            await utils.send_long_message(message.channel, f"```\n{help_message}\n```")
            logger.flush()
            return

        args = mdo_parser.parse_command(message)
        if isinstance(args, str):
            await utils.send_long_message(message.channel, f"```\n{args}\n```")
            return
        
        if args.wait:
            seconds = utils.parse_duration(args.wait)
            logger.INFO(f"Waiting for {args.wait} ({seconds} seconds) before executing command.")
            await asyncio.sleep(seconds)

        if args.schedule:
            try:
                seconds = utils.epoch_to(args.schedule)
                if seconds > 0:
                    logger.INFO(f"Scheduling command to run in {args.schedule} ({seconds} seconds).")
                    await asyncio.sleep(seconds)
                else:
                    logger.ERROR(f"Invalid schedule time: {args.schedule}. Must be greater than 0.")
            except Exception as e:
                logger.ERROR(f"Error parsing schedule time: {e}")
                logger.WARNING("Continuing without scheduling command.")

        if args.verbose:
            logger.set_level("VERBOSE")
        elif args.debug:
            logger.set_level("DEBUG")
        else:
            logger.set_level("INFO")
        logger.DEBUG(f"Debug args: {args}")
        # Execute the corresponding function from the COMMAND_MAP
        logger.VERBOSE(f"Executing command: {args.command}")
        logger.DEBUG(f"Link to message that trigger command: {message.jump_url}")
        logger.flush()

        if args.command in mdo_rework.COMMAND_MAP:
            if args.command == "help":
                help_message = await mdo_rework.help_command(args)
                await utils.send_long_message(message.channel, f"```\n{help_message}\n```")
                return
            
            channel = utils.get_channel(args.channel)
            if args.command in mdo_rework.REQUIRE_MFA and global_vars.MFA_STATUS:
                if not args.otp:
                    await message.channel.send(f"<@{message.author.id}> this command requires MFA. Please provide the OTP using `--otp <code>`.")
                    logger.ERROR(f"Command {args.command} requires MFA but no OTP provided.")
                    logger.flush()
                    return
                if not totp.validate_totp(args.otp):
                    await message.channel.send(f"<@{message.author.id}> invalid OTP code. Please try again.")
                    logger.ERROR(f"Invalid OTP code provided for command {args.command}.")
                    logger.flush()
                    return
            content = await mdo_rework.COMMAND_MAP[args.command](args)
            if content:
                mention_str = ""
                if len(args.mention) > 0:
                    mention_str = " ".join([f"<@{id}>" for id in args.mention])
                if args.everyone:
                    mention_str = "@everyone"
                
                if mention_str != "":
                    if args.after:
                        content = f"{content}\n{mention_str}"
                    else:
                        content = f"{mention_str}\n{content}"
                
                if not args.quiet:
                    if args.reply:
                        msg = await channel.fetch_message(args.reply)
                        if msg:
                            await msg.reply(content)
                        else:
                            await channel.send(content)
                    else:
                        await channel.send(content)
                logger.INFO("Executed: mdo " + args.command)
            if args.delete:
                await message.delete()
            logger.set_level("INFO")  # Reset log level after command execution
        else:
            logger.ERROR(f"Command not found: mdo {args.command}")
        logger.flush()  # Ensure all logs are sent
        
    else: # mbot command
        # catch the help command before parsing args
        # if the parser is get the help command, it will stop the whole process
        help_match = re.match(r"^mbot\s+([a-zA-Z0-9_-]+)\s+(?:-h|--help)\b", message.content)
        if help_match:
            help_message = mbot_parser.get_help_command(command)
            await utils.send_long_message(message.channel, f"```\n{help_message}\n```")
            return

        args = mbot_parser.parse_command(message)
        if isinstance(args, str):
            await utils.send_long_message(message.channel, f"```\n{args}\n```")
            return
        
        # print(args)
        
        if args.command in mbot_rework.MBOT_COMMAND_MAP:
            if args.command == "help":
                help_message = await mbot_rework.help_command(args)
                await utils.send_long_message(message.channel, f"```\n{help_message}\n```")
                return
            
            content = await mbot_rework.MBOT_COMMAND_MAP[args.command](args)
            await message.channel.send(content)
        else:
            await message.channel.send(f"Command not found: mbot {args.command}")

client.run(global_vars.TOKEN)
