import discord
import asyncio
import pytz

from datetime import datetime

class DiscordLogger:
    LEVELS = {
        "VERBOSE": 0,
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }

    EMOJIS = {
        "VERBOSE": "🔍",
        "DEBUG": "🐞",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥",
    }

    def __init__(self, log_channel: discord.TextChannel, level: str = "INFO", *, show_timestamp: bool = True):
        self.log_channel = log_channel
        self.level = self.LEVELS.get(level.upper(), 20)
        self.show_timestamp = show_timestamp
        self._buffer = ""
        self._queue = asyncio.Queue()
        self._started = False

    def set_level(self, level: str):
        self.level = self.LEVELS.get(level.upper(), self.level)

    def _get_timestamp(self):
        now_utc_plus_7 = datetime.now(pytz.timezone('Asia/Bangkok'))
        return f"[{now_utc_plus_7.strftime('%Y-%m-%d %H:%M:%S')} UTC+7] " if self.show_timestamp else ""

    def _start_worker(self):
        if not self._started:
            self._started = True
            asyncio.create_task(self._log_worker())

    def _enqueue_log(self, level: str, message: str):
        if self.LEVELS[level] < self.level:
            return

        self._start_worker()
        self._queue.put_nowait(("log", level, message))

    def flush(self):
        self._start_worker()
        self._queue.put_nowait(("flush", None, None))

    async def _log_worker(self):
        while True:
            task_type, level, message = await self._queue.get()

            if task_type == "log":
                await self._process_log(level, message)
            elif task_type == "flush":
                await self._process_flush()

    async def _process_log(self, level: str, message: str):
        timestamp = self._get_timestamp()
        formatted = f"{timestamp}- {self.EMOJIS[level]} **{level}**: {message}\n"

        if len(formatted) > 2000:
            print(f"Skipped log (too long): {formatted[:100]}...")
            return

        if len(self._buffer) + len(formatted) > 2000:
            await self._process_flush()

        self._buffer += formatted

    async def _process_flush(self):
        if not self._buffer.strip():
            return
        try:
            await self.log_channel.send(self._buffer.strip())
        except Exception as e:
            print(f"Failed to flush log to Discord: {e}")
        self._buffer = ""

    # Logging entrypoints
    def VERBOSE(self, message: str): self._enqueue_log("VERBOSE", message)
    def DEBUG(self, message: str): self._enqueue_log("DEBUG", message)
    def INFO(self, message: str): self._enqueue_log("INFO", message)
    def WARNING(self, message: str): self._enqueue_log("WARNING", message)
    def ERROR(self, message: str): self._enqueue_log("ERROR", message)
    def CRITICAL(self, message: str): self._enqueue_log("CRITICAL", message)
