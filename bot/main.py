import asyncio
import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from dotenv import load_dotenv

from bot.containers import Container
from bot.dialogs import register_dialogs
from bot.handlers import register_handlers
from bot.services.logger_service import LogEvent, LogLevel
from bot.utils.logging import setup_logging
from bot.utils.middlaware import MainMiddleware


async def main():
    load_dotenv()

    container = Container()
    bot = container.bot()

    telegram_logger = setup_logging(bot)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware.register(MainMiddleware(bot))
    register_handlers(dp)
    register_dialogs(dp)
    setup_dialogs(dp)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["my_chat_member", "message", "callback_query"],
            skip_updates=True,
        )
    except Exception as e:
        logging.error(f"Bot stopped with error: {e}")

        if telegram_logger and telegram_logger.enabled:
            await telegram_logger.log(
                LogEvent(
                    level=LogLevel.ERROR,
                    message="Bot stopped unexpectedly",
                    additional_data={"Error": str(e), "Status": "Offline"},
                )
            )
        raise
    finally:
        logging.info("Bot shutdown completed")


if __name__ == "__main__":
    asyncio.run(main())
