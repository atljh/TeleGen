import asyncio
import logging
import os
import sys
import time

from aiogram import Bot

from bot.containers import Container
from bot.database.exceptions import GenerationLimitExceeded
from bot.database.models import FlowDTO
from bot.database.models.post import PostDTO, PostStatus
from bot.services.flow_service import FlowService
from bot.services.logger_service import init_logger
from bot.services.post import PostService
from bot.utils.notifications import send_telegram_notification


async def generate_flow(
    flow_id: int,
    chat_id: int,
) -> list:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    try:
        flow_service = Container.flow_service()
        post_service = Container.post_service()
        flow = await flow_service.get_flow_by_id(flow_id)
        user = await flow_service.get_user_by_flow_id(flow.id)

        logging.info(
            f"User {user.username} started generation for flow {flow.name} ({flow.id})"
        )

        if not flow:
            await send_telegram_notification(
                bot_token, chat_id, f"❌ Флоу з ID {flow_id} не знайдено"
            )
            return []

        start_time = time.time()
        posts = await _start_telegram_generations(
            flow,
            flow_service,
            post_service,
            chat_id,
            bot_token,
            allow_partial=True,
            auto_generate=False,
        )
        posts_count = len(posts) if posts else 0
        logging.info(
            f"Generated {posts_count} posts for flow {flow.id} for {time.time() - start_time:.2f} sec"
        )

    except Exception as e:
        logging.error(f"Помилка генерації: {e!s}", exc_info=True)
        # await send_telegram_notification(
        #     bot_token,
        #     chat_id,
        #     f"❌ Критична помилка під час генерації флоу {flow_id}:\n_{e!s}_",
        #     parse_mode="Markdown",
        # )
        raise


async def _start_telegram_generations(
    flow: FlowDTO,
    flow_service: FlowService,
    post_service: PostService,
    chat_id: int | None,
    bot_token: str | None,
    allow_partial: bool = True,
    auto_generate: bool = False,
) -> list[PostDTO]:
    try:
        generated_posts = await post_service.generate_auto_posts(
            flow.id, allow_partial=allow_partial, auto_generate=auto_generate
        )
    except GenerationLimitExceeded as e:
        logging.warning(f"Flow {flow.id}: {e}")
        await flow_service.update_next_generation_time(flow.id)
        if chat_id and bot_token:
            await send_telegram_notification(
                bot_token, chat_id, str(e), parse_mode="MarkdownV2"
            )
        return []

    if not generated_posts:
        await flow_service.update_next_generation_time(flow.id)
        # Notify user that no posts were generated (if chat_id is available)
        if chat_id and bot_token:
            error_msg = (
                f"⚠️ *Генерація завершена без результатів*\n\n"
                f"Флоу: *{flow.name}*\n\n"
                f"❌ Сгенерованих постів не знайдено\\.\n\n"
                f"Можливі причини:\n"
                f"• Помилки обробки контенту\n"
                f"• Відсутність нових постів в джерелах\n\n"
            )
            await send_telegram_notification(
                bot_token, chat_id, error_msg, parse_mode="MarkdownV2"
            )
        return []

    # No deletion needed - dialogs will show only flow_volume posts
    # All posts are kept in DB as history/backup
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
        await generate_flow(flow_id, chat_id)

    asyncio.run(main())
