import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs

from bot.services.logger_service import LogEvent, LogLevel
from bot.utils.middlaware import MainMiddleware
from handlers import register_handlers
from bot.containers import Container
from bot.utils.logging import setup_logging
from dialogs import register_dialogs

async def main():
    load_dotenv()
    
    container = Container()
    bot = container.bot()
    
    telegram_logger = await setup_logging(bot)
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware.register(MainMiddleware(bot))
    register_handlers(dp)
    register_dialogs(dp)
    setup_dialogs(dp)
    
    if telegram_logger and telegram_logger.enabled:
        await telegram_logger.log(LogEvent(
            level=LogLevel.SUCCESS,
            message="Bot started and ready to receive updates",
            additional_data={
                "Status": "Online",
                "Updates": "message, callback_query, my_chat_member"
            }
        ))
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["my_chat_member", "message", "callback_query"],
            skip_updates=True
        )
    except Exception as e:
        logging.error(f"Bot stopped with error: {e}")
        
        if telegram_logger and telegram_logger.enabled:
            await telegram_logger.log(LogEvent(
                level=LogLevel.ERROR,
                message="Bot stopped unexpectedly",
                additional_data={
                    "Error": str(e),
                    "Status": "Offline"
                }
            ))
        raise
    finally:
        logging.info("Bot shutdown completed")
        
        if telegram_logger and telegram_logger.enabled:
            await telegram_logger.log(LogEvent(
                level=LogLevel.INFO,
                message="Bot shutdown completed",
                additional_data={
                    "Status": "Offline",
                    "Shutdown Time": "Graceful"
                }
            ))

if __name__ == "__main__":
    asyncio.run(main())