from aiogram import BaseMiddleware

class MainMiddleware(BaseMiddleware):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def __call__(self, handler, event, data):
        data["bot"] = self.bot
        return await handler(event, data)
