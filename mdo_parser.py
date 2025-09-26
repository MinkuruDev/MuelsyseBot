import argparse
import shlex
import discord
import io
import contextlib
import global_vars

# --- Global parser ---
global_parser = argparse.ArgumentParser(add_help=False)
global_parser.add_argument("-c", "--channel", help="Channel to send output message to")
global_parser.add_argument("-g", "--guild", type=int, default=global_vars.MMM_SERVER_ID, help="Guild ID in the context of the command")
global_parser.add_argument("-d", "--delete", action="store_true", help="Delete original message")
global_parser.add_argument("-m", "--mention", action="append", default=None, help="Mention role or member (append mode)")
global_parser.add_argument("-e", "--everyone", action="store_true", help="Mention everyone")
global_parser.add_argument("-a", "--after", action="store_true", help="Mention in the end of the message")
global_parser.add_argument("-q", "--quiet", action="store_true", help="Do not output message")
global_parser.add_argument("-r", "--reply", type=int, help="Reply to specific message ID")
# --- Special arguments ---
global_parser.add_argument("-D", "--debug", action="store_true", default=(global_vars.RELEASE==0), help="Execute in debug mode")
global_parser.add_argument("-V", "--verbose", action="store_true", help="Verbose logging")
global_parser.add_argument("-W", "--wait", help="Wait for the provided time (duration, ex: 1h30m5s) before executing the command")
global_parser.add_argument("-S", "--schedule", help="Schedule time (in the time format: HH:MM:SS-dd/mm/yyyy) to execute the command")
global_parser.add_argument("-O", "--otp", type=str, help="OTP code for MFA (if enabled)")

# --- Main parser ---
parser = argparse.ArgumentParser(prog="mdo", description="mdo command parser", parents=[global_parser])
subparsers = parser.add_subparsers(dest="command", required=True)

# Subparser reference (for custom help command)
subparser_map = {}

# --- edit ---
edit = subparsers.add_parser("edit", help="Edit a message", parents=[global_parser])
edit.add_argument("message_channel", help="Channel or channel ID containing the message to edit")
edit.add_argument("message_id", type=int,help="Message ID to edit")
edit.add_argument("context", nargs=argparse.REMAINDER, help="Context to edit")
edit.add_argument("-f", "--file", help="Edit using content in the text file")
subparser_map["edit"] = edit

# --- announcement ---
announcement = subparsers.add_parser("announcement", help="Send content of the file announcement.md to announcement channel", parents=[global_parser])
subparser_map["announcement"] = announcement

# --- facebook ---
facebook = subparsers.add_parser("facebook", help="Fetch latest MWC Facebook post", parents=[global_parser])
subparser_map["facebook"] = facebook

# --- help ---
help_cmd = subparsers.add_parser("help", help="Show help for a command", parents=[global_parser])
help_cmd.add_argument("cmd", nargs="?", default=None, help="Command name to show help for")
subparser_map["help"] = help_cmd

# --- send ---
send = subparsers.add_parser("send", help="Send a message or file", parents=[global_parser])
send.add_argument("context", nargs=argparse.REMAINDER, help="Context to send")
send.add_argument("-i", "--image", help="Image path or URL")
send.add_argument("-f", "--file", help="Send text content from a file")
subparser_map["send"] = send

# --- timeout ---
timeout = subparsers.add_parser("timeout", help="Timeout a member", parents=[global_parser])
timeout.add_argument("member", help="Member or member id to timeout")
timeout.add_argument("duration", help="Duration to timeout (e.g., 1h, 30m, 15s, 1d12h30m6s)")
timeout.add_argument("reason", nargs=argparse.REMAINDER, help="Reason for timeout")
subparser_map["timeout"] = timeout

# --- nickname ---
nickname = subparsers.add_parser("nickname", help="Set nicknames", parents=[global_parser])
subparser_map["nickname"] = nickname

# --- birthday ---
birthday = subparsers.add_parser("birthday", help="Set/remove birthday roles", parents=[global_parser])
subparser_map["birthday"] = birthday

# --- set-birthday ---
set_birthday = subparsers.add_parser("set-birthday", help="Set birthday", parents=[global_parser])
set_birthday.add_argument("member", help="Member or member ID to set birthday for")
set_birthday.add_argument("day", type=int, help="Day of the month")
set_birthday.add_argument("month", type=int, help="Month of the year")
subparser_map["set-birthday"] = set_birthday

# --- anniversary ---
anniversary = subparsers.add_parser("anniversary", help="Check for anniversary and annouce", parents=[global_parser])
subparser_map["anniversary"] = anniversary

# --- leaderboard ---
index_lb = subparsers.add_parser("index-lb", help="Indexing leaderboard for selected month and year", parents=[global_parser])
index_lb.add_argument("month", type=int, help="Month of the year")
index_lb.add_argument("year", type=int, help="Year")
index_lb.add_argument("-s", "--sam-diff", default=0, type=int, help="Super Active Month difficulty")
subparser_map["index-lb"] = index_lb

# --- leaderboard ---
leaderboard = subparsers.add_parser("leaderboard", help="Generate message leaderboard", parents=[global_parser])
leaderboard.add_argument("month", type=int, help="Month of the year")
leaderboard.add_argument("year", type=int, help="Year")
leaderboard.add_argument("-s", "--sam-diff", default=0, type=int, help="Super Active Month difficulty")
subparser_map["leaderboard"] = leaderboard

# --- fix ---
fix = subparsers.add_parser("fix", help="Fix member roles", parents=[global_parser])
subparser_map["fix"] = fix

# --- prune ---
prune = subparsers.add_parser("prune", help="Delete member messages", parents=[global_parser])
prune.add_argument("member", help="Member or member ID to prune messages for")
prune.add_argument("number", type=int, help="Number of messages to delete")
prune.add_argument("-l", "--limit", type=int, default=50, help="Limit of messages to check")
subparser_map["prune"] = prune

# --- mfa ---
mfa = subparsers.add_parser("mfa", help="Show or enable/disable MFA", parents=[global_parser])
mfa.add_argument("--enable", action="store_true", help="Enable MFA")
mfa.add_argument("--disable", action="store_true", help="Disable MFA")
subparser_map["mfa"] = mfa

# --- kick ---
kick = subparsers.add_parser("kick", help="Kick a member", parents=[global_parser])
kick.add_argument("member", help="Member or member ID to kick")
kick.add_argument("reason", nargs=argparse.REMAINDER, help="Reason for kick")
subparser_map["kick"] = kick

# --- ban ---
ban = subparsers.add_parser("ban", help="Ban a member", parents=[global_parser])
ban.add_argument("member", help="Member or member ID to ban")
ban.add_argument("reason", nargs=argparse.REMAINDER, help="Reason for ban")
subparser_map["ban"] = ban

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
    if not content.startswith("mdo "):
        print(f"Not a command: {content}")
        return None  # Not a command

    args_str = content[len("mdo "):]
    try:
        args_list = args_str.split(" ")
        with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                args = parser.parse_args(args_list)
                if args.guild is None:
                    args.guild = message.guild.id
                if args.channel is None:
                    args.channel = message.channel.id
                if args.mention is None:
                    args.mention = []
                return args
            except SystemExit:
                # argparse threw an error or printed help, safely return error message
                return buf.getvalue()
    except Exception as e:
        print(f"Error parsing command: {e}")
        return f"Error parsing command: {e}"
    
def parse_str_command(command: str):
    if not command.startswith("mdo "):
        print(f"Not a command: {command}")
        return None  # Not a command

    args_str = command[len("mdo "):]
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
