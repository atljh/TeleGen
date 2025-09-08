import time
from typing import Dict, List, Optional

from bot.database.models.flow import FlowDTO
from bot.database.models.post import PostDTO
from bot.services.telegram_userbot.core.base_userbot_service import BaseUserbotService
from bot.services.telegram_userbot.processing.content_processing_service import (
    ContentProcessingService,
)
from bot.services.telegram_userbot.processing.post_conversion_service import (
    PostConversionService,
)


class EnhancedUserbotService(BaseUserbotService):
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        aisettings_service: "AISettingsService",
        user_service: "UserService",
        openai_key: str = None,
        **kwargs,
    ):
        super().__init__(api_id, api_hash, **kwargs)

        self.content_processor = ContentProcessingService(
            openai_key=openai_key,
            aisettings_service=aisettings_service,
            user_service=user_service,
        )

        self.post_converter = PostConversionService(self.content_processor)

        self.user_service = user_service
        self.aisettings_service = aisettings_service
        self.openai_key = openai_key

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            start_time = time.time()

            raw_posts = await super().get_last_posts(flow.sources, limit)

            processed_posts = await self.post_converter.convert_raw_posts_to_dto(
                raw_posts, flow
            )

            self.logger.info(
                f"[Telegram] Processed {len(processed_posts)} posts "
                f"in {time.time() - start_time:.2f}s"
            )

            return processed_posts

        except Exception as e:
            self.logger.error(f"Error getting posts: {str(e)}", exc_info=True)
            return []

    async def process_content(self, text: str, flow: FlowDTO) -> str:
        return await self.content_processor.process_post_content(
            PostDTO(content=text), flow
        ).content

    async def convert_raw_post(
        self, raw_post: Dict, flow: FlowDTO
    ) -> Optional[PostDTO]:
        return await self.post_converter._convert_single_post(raw_post, flow)
