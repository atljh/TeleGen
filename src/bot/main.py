import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs

from bot.utils.middlaware import MainMiddleware
from handlers import register_handlers
from bot.containers import Container
from bot.utils.logging import setup_logging
from dialogs import register_dialogs

async def main():
    container = Container()
    
    bot = container.bot()
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware.register(MainMiddleware(bot))
    register_handlers(dp)
    register_dialogs(dp)
    setup_dialogs(dp)
    
    setup_logging()
    
    await dp.start_polling(
        bot,
        allowed_updates=["my_chat_member", "message", "callback_query"],
        skip_updates=True
    )

if __name__ == "__main__":
    asyncio.run(main())