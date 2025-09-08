import asyncio
import logging

from aiogram import Bot

from bot.services.logger_service import LogEvent, LogLevel, get_logger, init_logger


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
                task = asyncio.create_task(self.logger_service.log(event))
                task.add_done_callback(lambda t: t.exception() and None)

            except Exception:
                pass


def setup_logging(bot: Bot):
    init_logger(bot)
    telegram_logger = get_logger()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("bot.log", encoding="utf-8"),
        ],
    )

    telegram_handler = TelegramLogHandler(bot)
    telegram_handler.set_logger_service(telegram_logger)
    telegram_handler.setFormatter(
        logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return telegram_logger
