import os
import sys
import asyncio
import logging
import time
from typing import List
from pathlib import Path
from logging.handlers import RotatingFileHandler

from bot.containers import Container
from bot.utils.notifications import send_telegram_notification

def setup_logging(flow_id: int):
    log_dir = Path("/app/logs/generation")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    file_handler = RotatingFileHandler(
        log_dir / f"flow_{flow_id}.log",
        maxBytes=5*1024*1024,
        backupCount=3
    )
    
    class FlushingStreamHandler(logging.StreamHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()
    
    console_handler = FlushingStreamHandler(sys.stdout)
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S'
    )
    
    for handler in [file_handler, console_handler]:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

async def generate_flow(
    flow_id: int,
    chat_id: int,
) -> List:
    try:
        setup_logging(flow_id)
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        flow_service = Container.flow_service()
        post_service = Container.post_service()
        flow = await flow_service.get_flow_by_id(flow_id)
        logging.info(f"[Генерация] Начало обработки флоу {flow_id}")
        if not flow:
            await send_telegram_notification(
                bot_token,
                chat_id,
                f"❌ Флоу з ID {flow_id} не знайдено"
            )
            return
        start_time = time.time()
        posts = await _start_telegram_generations(
            flow,
            flow_service,
            post_service
        )
        posts_count = len(posts) if posts else 0
        logging.info(f"Генерация заняла {time.time() - start_time:.2f} сек")

    except Exception as e:
        logging.error(f"Помилка генерації: {str(e)}", exc_info=True)
        await send_telegram_notification(
            bot_token,
            chat_id,
            f"❌ Критична помилка під час генерації флоу {flow_id}:\n"
            f"_{str(e)}_",
            parse_mode="Markdown"
        )
        raise

async def _start_telegram_generations(
    flow,
    flow_service,
    post_service
) -> List:

    existing_posts = await post_service.get_all_posts_in_flow(flow.id)
    existing_count = len(existing_posts)
    
    generated_posts = await post_service.generate_auto_posts(flow.id)
    if not generated_posts:
        logging.info(f"No posts generated for flow {flow.id}")
        return
    
    total_after_generation = existing_count + len(generated_posts)
    overflow = total_after_generation - flow.flow_volume
    
    if overflow > 0:
        posts_to_delete = min(overflow, existing_count)
        if posts_to_delete > 0:
            old_posts = existing_posts[:posts_to_delete]
            logging.info(f"Deleting {len(old_posts)} oldest posts from flow {flow.id}")
            
            for post in old_posts:
                await post_service.delete_post(post.id)
    
    await flow_service.update_next_generation_time(flow.id)

    return generated_posts

if __name__ == "__main__":
    flow_id = int(sys.argv[1])
    chat_id = int(sys.argv[2])
    asyncio.run(generate_flow(flow_id, chat_id))