import logging
from rich.logging import RichHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logging.getLogger("aiogram").setLevel(logging.WARNING)
