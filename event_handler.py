import asyncio
import discord

class EventHandler:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, func):
        if func not in self.subscribers:
            self.subscribers.append(func)

    def unsubscribe(self, func):
        if func in self.subscribers:
            self.subscribers.remove(func)

    async def invoke(self, *args, **kwargs):
        for sub in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(sub):
                    asyncio.create_task(sub(*args, **kwargs))
                else:
                    sub(*args, **kwargs)
            except Exception as e:
                print(f"Error in event subscriber: {e}")

class MessageEventHandler(EventHandler):
    def __init__(self):
        super().__init__()

    async def invoke(self, message: discord.Message, logger=None):
        for sub in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(sub):
                    asyncio.create_task(sub(message))
                else:
                    sub(message)
            except Exception as e:
                if logger:
                    logger.ERROR(f"Error in message subscriber: {e}")
                else:
                    print(f"Error in message subscriber: {e}")
