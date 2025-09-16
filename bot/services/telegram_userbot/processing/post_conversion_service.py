from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.services.telegram_userbot.processing.content_processing_service import (
        ContentProcessingService,
    )

from bot.database.models import FlowDTO, PostDTO


class PostConversionService:
    def __init__(self, content_processor: ContentProcessingService):
        self.content_processor = content_processor
        self.logger = logging.getLogger(__name__)

    async def convert_raw_posts_to_dto(
        self, raw_posts: list[dict], flow: FlowDTO
    ) -> list[PostDTO]:
        tasks = []
        for raw_post in raw_posts:
            if not raw_post:
                continue
            task = self._safe_convert_post(raw_post, flow)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, PostDTO)]

    async def _safe_convert_post(self, raw_post: dict, flow: FlowDTO) -> PostDTO | None:
        try:
            return await self._convert_single_post(raw_post, flow)
        except Exception as e:
            self.logger.warning(f"Post conversion failed: {e}")
            return None

    async def _convert_single_post(
        self, raw_post: dict, flow: FlowDTO
    ) -> PostDTO | None:
        post_dto = PostDTO.from_raw_post(raw_post)
        logging.info(post_dto)
        if not post_dto.content:
            return None

        post_dto = self._set_post_metadata(post_dto, raw_post)

        return await self.content_processor.process_post_content(post_dto, flow)

    def _set_post_metadata(self, post_dto: PostDTO, raw_post: dict) -> PostDTO:
        update_data = {}

        if "original_link" in raw_post:
            update_data["original_link"] = raw_post["original_link"]
        if "original_date" in raw_post:
            update_data["original_date"] = raw_post["original_date"]
        if "source_url" in raw_post:
            update_data["source_url"] = raw_post["source_url"]
        if "source_id" in raw_post:
            update_data["source_id"] = raw_post["source_id"]
        if "original_content" in raw_post:
            update_data["original_content"] = raw_post["original_content"]

        update_data.update(
            {
                "flow_id": post_dto.flow_id,
                "original_content": post_dto.original_content
                or raw_post.get("original_content", ""),
            }
        )

        return post_dto.copy(update=update_data)
