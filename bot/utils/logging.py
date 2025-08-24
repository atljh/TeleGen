import asyncio
import logging
from aiogram import Bot
from bot.services.logger_service import LogEvent, LogLevel, init_logger, get_logger

class TelegramLogHandler(logging.Handler):
    
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot
        self.logger_service = None
        
    def set_logger_service(self, logger_service):
        self.logger_service = logger_service
    
    def emit(self, record):
        if self.logger_service and self.logger_service.enabled:
            level_mapping = {
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.ERROR,
            }
            
            log_level = level_mapping.get(record.levelno, LogLevel.INFO)
            
            event = LogEvent(
                level=log_level,
                message=self.format(record),
            )
            
            try:
                asyncio.create_task(self.logger_service.log(event))
            except:
                pass

async def setup_logging(bot: Bot):
    
    init_logger(bot)
    telegram_logger = get_logger()
    
    if telegram_logger and telegram_logger.enabled:
        await telegram_logger.log(LogEvent(
            level=LogLevel.SYSTEM,
            message="Bot instance starting up",
            additional_data={
                "Status": "Initializing",
                "Log Level": "INFO"
            }
        ))
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            # logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    telegram_handler = TelegramLogHandler(bot)
    telegram_handler.set_logger_service(telegram_logger)
    telegram_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.addHandler(telegram_handler)
    root_logger.setLevel(logging.INFO)
    
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    
    return telegram_logger