import logging
import time

from aiogram import Bot

from bot.database.models.flow import FlowDTO
from bot.database.models.post import PostDTO
from bot.services.aisettings_service import AISettingsService
from bot.services.telegram_userbot.core.base_userbot_service import BaseUserbotService
from bot.services.telegram_userbot.processing.content_processing_service import (
    ContentProcessingService,
)
from bot.services.telegram_userbot.processing.post_conversion_service import (
    PostConversionService,
)
from bot.services.user_service import UserService


class EnhancedUserbotService(BaseUserbotService):
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        aisettings_service: "AISettingsService",
        user_service: "UserService",
        bot: Bot,
        openai_key: str | None = None,
        logger: logging.Logger | None = None,
        **kwargs,
    ):
        super().__init__(api_id, api_hash, bot, **kwargs)

        self.content_processor = ContentProcessingService(
            openai_key=openai_key,
            aisettings_service=aisettings_service,
            user_service=user_service,
        )

        self.post_converter = PostConversionService(self.content_processor)
        self.logger = logger or logging.getLogger(__name__)
        self.bot = bot
        self.user_service = user_service
        self.aisettings_service = aisettings_service
        self.openai_key = openai_key

    async def get_last_posts(
        self, flow: FlowDTO, source: dict, limit: int = 10
    ) -> list[PostDTO]:
        try:
            start_time = time.time()

            raw_posts = await super().get_last_posts(source, limit)

            processed_posts = await self.post_converter.convert_raw_posts_to_dto(
                raw_posts, flow
            )

            if len(raw_posts) > 0 and len(processed_posts) == 0:
                self.logger.warning(
                    f"[Telegram] Source {source['link']}: received {len(raw_posts)} raw posts "
                    f"but ALL failed AI processing (likely quota/API errors)"
                )
            else:
                self.logger.warning(
                    f"[Telegram] Source {source['link']}: processed {len(processed_posts)}/{len(raw_posts)} posts "
                    f"in {time.time() - start_time:.2f}s"
                )
            return processed_posts

        except Exception as e:
            self.logger.error(
                f"Error getting posts from source {source['link']}: {e!s}",
                exc_info=True,
            )
            return []

    async def process_content(self, text: str, flow: FlowDTO) -> str:
        post = await self.content_processor.process_post_content(
            PostDTO(content=text), flow
        )
        return post.content

    async def convert_raw_post(self, raw_post: dict, flow: FlowDTO) -> PostDTO | None:
        return await self.post_converter._convert_single_post(raw_post, flow)

    async def __aenter__(self):
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
