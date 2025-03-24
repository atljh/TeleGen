import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram_dialog import setup_dialogs

from handlers import register_handlers
from bot.containers import Container
from bot.utils.logging import setup_logging
from handlers.generation import register_generation
from dialogs import register_dialogs

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    session = AiohttpSession()
    bot = Bot(token=API_TOKEN, session=session)
    dp = Dispatcher()

    register_dialogs(dp)
    setup_dialogs(dp)

    dp.include_router(register_handlers()) 
    container = Container()
    
    setup_logging()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())