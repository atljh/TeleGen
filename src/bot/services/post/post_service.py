from datetime import datetime

from aiogram import Bot

from bot.database.exceptions import InvalidOperationError, PostNotFoundError
from bot.database.models import PostDTO, PostStatus
from bot.database.repositories import FlowRepository, PostRepository
from bot.services.media_service import MediaService
from bot.services.post.base import PostBaseService
from bot.services.post.generation import PostGenerationService
from bot.services.post.publish import PostPublishingService
from bot.services.post.scheduling import PostSchedulingService
from bot.services.telegram_userbot.enhanced_userbot_service import (
    EnhancedUserbotService,
)
from bot.services.web.web_service import WebService


class PostService:
    def __init__(
        self,
        bot: Bot,
        web_service: WebService,
        userbot_service: EnhancedUserbotService,
        post_repository: PostRepository,
        flow_repository: FlowRepository,
    ) -> None:
        self.bot = bot
        self.flow_repo = flow_repository
        self.media_service = MediaService()
        self.base_service = PostBaseService(post_repository, self.media_service)
        self.publishing_service = PostPublishingService(bot, self.base_service)
        self.scheduling_service = PostSchedulingService(
            self.base_service, self.publishing_service
        )
        self.generation_service = PostGenerationService(
            userbot_service, web_service, flow_repository, self.base_service, bot
        )

    async def get_post(self, post_id: int) -> PostDTO:
        return await self.base_service.get_post(post_id)

    async def update_post(self, post_id: int, **kwargs) -> PostDTO:
        return await self.base_service.update_post(post_id, **kwargs)

    async def delete_post(self, post_id: int) -> None:
        await self.base_service.delete_post(post_id)

    async def get_all_posts_in_flow(
        self, flow_id: int, status: PostStatus
    ) -> list[PostDTO]:
        return await self.base_service.get_all_posts_in_flow(flow_id, status)

    async def publish_post(self, post_id: int, channel_id: str) -> PostDTO:
        return await self.publishing_service.publish_post(post_id, channel_id)

    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> PostDTO:
        return await self.scheduling_service.schedule_post(post_id, scheduled_time)

    async def update_post_status(self, post_id: int, status: PostStatus) -> PostDTO:
        return await self.base_service.update_post_status(post_id, status)

    async def publish_scheduled_posts(self) -> list[PostDTO]:
        return await self.scheduling_service.publish_scheduled_posts()

    async def generate_auto_posts(
        self,
        flow_id: int,
        allow_partial: bool = False,
        auto_generate: bool = False,
    ) -> list[PostDTO]:
        return await self.generation_service.generate_auto_posts(
            flow_id, allow_partial, auto_generate
        )

    async def create_post(
        self,
        flow_id: int,
        content: str,
        original_content: str | None = None,
        original_link: str | None = None,
        original_date: datetime | None = None,
        source_url: str | None = None,
        media_list: list[dict] | None = None,
        status: PostStatus | None = None,
        scheduled_time: datetime | None = None,
        source_id: str | None = None,
    ) -> PostDTO:
        if not await self.flow_repo.exists(flow_id):
            raise PostNotFoundError(f"Flow with id {flow_id} not found")

        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        flow = await self.flow_repo.get_flow_by_id(flow_id)
        return await self.base_service.create_post(
            flow=flow,
            content=content,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_url=source_url,
            media_list=media_list,
            status=status,
            scheduled_time=scheduled_time,
            source_id=source_id,
        )
