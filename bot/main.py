import os
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
import logging
import asyncio
from dotenv import load_dotenv
from aiogram_dialog import setup_dialogs

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    session = AiohttpSession()
    bot = Bot(token=API_TOKEN, session=session)
    dp = Dispatcher()

    from dialogs.main_dialog import main_dialog
    dp.include_router(main_dialog)

    setup_dialogs(dp)

    from handlers import start
    start.register_handlers(dp)

    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())