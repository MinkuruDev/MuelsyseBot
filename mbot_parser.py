import argparse
import discord
import io
import contextlib
import global_vars

# --- Global parser ---
global_parser = argparse.ArgumentParser(add_help=False)

# --- Main parser ---
parser = argparse.ArgumentParser(prog="mbot", description="mbot command usage:", parents=[global_parser])
subparsers = parser.add_subparsers(dest="command", required=True)

# Subparser reference (for custom help command)
subparser_map = {}

# --- help ---
help_cmd = subparsers.add_parser("help", help="Show help for a command", parents=[global_parser])
help_cmd.add_argument("cmd", nargs="?", default=None, help="Command name to show help for")
subparser_map["help"] = help_cmd

# --- set-birthday ---
set_birthday = subparsers.add_parser("set-birthday", help="Set your birthday", parents=[global_parser])
set_birthday.add_argument("day", type=int, help="Day of the month")
set_birthday.add_argument("month", type=int, help="Month of the year")
subparser_map["set-birthday"] = set_birthday

# --- check-birthday ---
check_birthday = subparsers.add_parser("check-birthday", help="See someone birthday (if already set)", parents=[global_parser])
check_birthday.add_argument("user", nargs="?", default=None, help="User or user ID to see birthday for, leave empty to see your own birthday")
subparser_map["check-birthday"] = check_birthday

# --- set-number ---
set_number = subparsers.add_parser("set-number", help="Set your nickname number", parents=[global_parser])
set_number.add_argument("number", type=int, nargs="?", default=None, help="Number to set in nickname")
set_number.add_argument("-d", "--delete", action="store_true", default=False, help="Delete the number from nickname")
subparser_map["set-number"] = set_number

# --- ranking ---
ranking = subparsers.add_parser("ranking", help="See your leaderboard ranking in specified month and year", parents=[global_parser])
ranking.add_argument("month", type=int, nargs="?", default=None, help="Month to see ranking (1-12). Leave empty for last month")
ranking.add_argument("year", type=int, nargs="?", default=None, help="Year to see ranking (e.g., 2023). Leave empty for last month")
subparser_map["ranking"] = ranking

# --- muzzled ---
muzzled = subparsers.add_parser("muzzled", help="Try to muzzled a member", parents=[global_parser])
muzzled.add_argument("target", help="Target or target id to muzzled")
muzzled.add_argument("reason", nargs=argparse.REMAINDER, help="Reason for muzzled")
subparser_map["muzzled"] = muzzled

def get_help_command(command_name: str = None):
    """
    Get the help command for a specific command.
    :param command_name: The name of the command to get help for.
    :return: The help command object or None if not found.
    """
    buf = io.StringIO()
    if command_name is None:
        parser.print_help(file=buf)
    elif command_name in subparser_map:
        subparser_map[command_name].print_help(file=buf)
    else:
        buf.write(f"Unknown command: `{command_name}`\n\n")
        parser.print_help(file=buf)
    return buf.getvalue()

def parse_command(message: discord.Message):
    """
    Parse a command from a Discord message.
    :param message: The Discord message to parse.
    :return: Parsed arguments or None if parsing fails.
    """
    content = message.content.strip()
    if not content.startswith("mbot"):
        print(f"Not a command: {content}")
        return None  # Not a command

    args_str = content[len("mbot "):]
    try:
        args_list = args_str.split(" ")
        with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                args = parser.parse_args(args_list)
                args.member = message.author.id
                args.guild = message.guild.id
                args.channel = message.channel.id
                return args
            except SystemExit:
                # argparse threw an error or printed help, safely return error message
                return buf.getvalue()
    except Exception as e:
        print(f"Error parsing command: {e}")
        return f"Error parsing command: {e}"
    
def parse_str_command(command: str):
    if not command.startswith("mbot "):
        print(f"Not a command: {command}")
        return None  # Not a command

    args_str = command[len("mbot "):]
    try:
        args_list = args_str.split(" ")
        with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                args = parser.parse_args(args_list)
                return args
            except SystemExit:
                # argparse threw an error or printed help, safely return error message
                return buf.getvalue()
    except Exception as e:
        print(f"Error parsing command: {e}")
        return f"Error parsing command: {e}"
