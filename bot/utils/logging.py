import logging
from pathlib import Path
import os

def init_logging():
    log_dir_str = os.getenv('LOG_DIR', '/app/logs')
    log_dir = Path(log_dir_str)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"Log directory created: {log_dir}")
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

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    try:
        log_file = log_dir / "bot.log"
        print(f"Log file path: {log_file}")
        
        fh = logging.FileHandler(log_file, encoding="utf-8", mode='a')  # 'a' для append
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)
        
    except Exception as e:
        print(f"Failed to create file handler: {e}")

    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info("Logging initialized successfully")