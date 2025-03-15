import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
from aiogram_dialog import setup_dialogs

from handlers import start
from bot.containers import Container
from bot.utils.logging import setup_logging

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    session = AiohttpSession()
    bot = Bot(token=API_TOKEN, session=session)
    dp = Dispatcher()

    from dialogs.main_dialog import main_dialog
    dp.include_router(main_dialog)

    setup_dialogs(dp)

    container = Container()
    start.register_handlers(dp)

    setup_logging()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())