import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logging.getLogger("aiogram").setLevel(logging.DEBUG)