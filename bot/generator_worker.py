import os
import sys
import asyncio
import logging
import time
from typing import List
from pathlib import Path
from logging.handlers import RotatingFileHandler
from aiogram import Bot
from asgiref.sync import sync_to_async

from bot.containers import Container
from bot.database.models import FlowDTO
from bot.services.flow_service import FlowService
from bot.services.post import PostService
from bot.utils.notifications import send_telegram_notification
from bot.services.logger_service import (
    LogEvent, LogLevel, TelegramLogger,
    init_logger, get_logger
)

class TelegramLogHandler(logging.Handler):
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot
        self.logger_service = get_logger()

    def emit(self, record: logging.LogRecord):
        if not self.logger_service or not self.logger_service.enabled:
            return

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._send_log(record))
            else:
                loop.run_until_complete(self._send_log(record))
        except Exception as e:
            sys.stderr.write(f"[TelegramLogHandler ERROR] {e}\n")

    async def _send_log(self, record: logging.LogRecord):
        try:
            log_level = {
                logging.INFO: LogLevel.INFO,
            }.get(record.levelno, LogLevel.INFO)

            event = LogEvent(
                level=log_level,
                message=self.format(record)
            )
            await self.logger_service.log(event)
        except Exception as e:
            sys.stderr.write(f"[TelegramLogHandler async ERROR] {e}\n")


def setup_logging(bot: Bot = None):
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    class FlushingStreamHandler(logging.StreamHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()

    console_handler = FlushingStreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s | %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    return logger

async def generate_flow(
    flow_id: int,
    chat_id: int,
    bot: Bot,
    status_msg_id: int
) -> List:
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        flow_service = Container.flow_service()
        post_service = Container.post_service()
        flow = await flow_service.get_flow_by_id(flow_id)
        user = await flow_service.get_user_by_flow_id(flow.id)

        logging.info(f"User {user.username} started generation for flow {flow.name} ({flow.id})")

        if not flow:
            await send_telegram_notification(
                bot_token,
                chat_id,
                f"❌ Флоу з ID {flow_id} не знайдено"
            )
            return []

        start_time = time.time()
        posts = await _start_telegram_generations(
            flow,
            flow_service,
            post_service
        )
        posts_count = len(posts) if posts else 0
        logging.info(f"Generated {posts_count} posts for flow {flow.id} for {time.time() - start_time:.2f} sec")

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
    flow: FlowDTO,
    flow_service: FlowService,
    post_service: PostService,
    auto_generate = False
) -> List:

    existing_posts = await post_service.get_all_posts_in_flow(flow.id)
    existing_count = len(existing_posts)

    user = await flow_service.get_user_by_flow_id(flow.id)

    generated_posts = await post_service.generate_auto_posts(
        flow.id,
        auto_generate
    )
    generated_count = len(generated_posts) if generated_posts else 0

    if not generated_posts:
        await flow_service.update_next_generation_time(flow.id)
        return []

    total_after_generation = existing_count + generated_count
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
    status_msg_id = int(sys.argv[3])
    bot_token = sys.argv[4]

    bot = Bot(token=bot_token)

    async def main():
        init_logger(bot)
        await generate_flow(flow_id, chat_id, bot, status_msg_id)

    asyncio.run(main())