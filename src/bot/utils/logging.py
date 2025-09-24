import logging
import os
from pathlib import Path


def init_logging():
    log_dir_str = os.getenv("LOG_DIR", "/app/logs")
    log_dir = Path(log_dir_str)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Failed to create log directory: {e}")
        return

    if not os.access(log_dir, os.W_OK):
        print(f"No write permissions for: {log_dir}")
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    try:
        log_file = log_dir / "bot.log"

        fh = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)

    except Exception as e:
        print(f"Failed to create file handler: {e}")

    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("rss_service").setLevel(logging.INFO)

    logging.info("Logging initialized successfully")
