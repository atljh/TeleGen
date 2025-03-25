import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs

from handlers import register_handlers
from bot.containers import Container
from bot.utils.logging import setup_logging
from dialogs import register_dialogs

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    session = AiohttpSession()
    bot = Bot(token=API_TOKEN, session=session)
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    register_dialogs(dp)
    
    setup_dialogs(dp)

    dp.include_router(register_handlers())
    
    container = Container()
    
    setup_logging()
    
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())