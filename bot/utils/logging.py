import logging
from bot.services.logger_service import LogEvent, LogLevel, init_logger, get_logger

async def setup_logging(bot):

    init_logger(bot)
    logger = get_logger()
    
    if logger and logger.enabled:
        await logger.log(LogEvent(
            level=LogLevel.INFO,
            message="Bot started"
        ))
        
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logging.getLogger("aiogram").setLevel(logging.WARNING)