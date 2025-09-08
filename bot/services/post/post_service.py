from datetime import datetime
from typing import List, Optional

from aiogram import Bot
from asgiref.sync import sync_to_async

from admin_panel.admin_panel.models import Post, PostImage
from bot.database.exceptions import InvalidOperationError, PostNotFoundError
from bot.database.models import PostDTO, PostStatus
from bot.database.repositories import FlowRepository, PostRepository
from bot.services.post import (
    PostBaseService,
    PostGenerationService,
    PostPublishingService,
    PostSchedulingService,
)
from bot.services.web.web_service import WebService


class PostService:
    def __init__(
        self,
        bot: Bot,
        web_service: WebService,
        userbot_service: "EnhancedUserbotService",
        post_repository: PostRepository,
        flow_repository: FlowRepository,
    ):
        self.flow_repo = flow_repository
        self.bot = bot

        self.base_service = PostBaseService(post_repository)
        self.publishing_service = PostPublishingService(bot, self.base_service)
        self.scheduling_service = PostSchedulingService(
            self.base_service, self.publishing_service
        )
        self.generation_service = PostGenerationService(
            userbot_service, web_service, flow_repository, self.base_service, self.bot
        )

    async def get_post(self, post_id: int) -> PostDTO:
        return await self.base_service.get_post(post_id)

    async def update_post(self, post_id: int, **kwargs) -> PostDTO:
        return await self.base_service.update_post(post_id, **kwargs)

    async def delete_post(self, post_id: int) -> None:
        return await self.base_service.delete_post(post_id)

    async def publish_post(self, post_id: int, channel_id: str) -> PostDTO:
        return await self.publishing_service.publish_post(post_id, channel_id)

    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> PostDTO:
        return await self.scheduling_service.schedule_post(post_id, scheduled_time)

    async def publish_scheduled_posts(self) -> List[PostDTO]:
        return await self.scheduling_service.publish_scheduled_posts()

    async def generate_auto_posts(
        self, flow_id: int, auto_generate: bool = False
    ) -> list[PostDTO]:
        return await self.generation_service.generate_auto_posts(flow_id, auto_generate)

    async def get_all_posts_in_flow(self, flow_id: int) -> List[Post]:
        return await sync_to_async(list)(
            Post.objects.filter(flow_id=flow_id).order_by("created_at")
        )

    async def get_oldest_posts(self, flow_id: int, limit: int) -> List[Post]:
        return await sync_to_async(list)(
            Post.objects.filter(flow_id=flow_id).order_by("created_at")[:limit]
        )

    async def update_post_with_media(
        self, post_id: int, content: str, media_list: List[dict]
    ) -> PostDTO:
        post = await self.base_service.post_repo.get(post_id)

        post.content = content
        await sync_to_async(post.save)()

        await sync_to_async(lambda: post.images.all().delete())()

        for media in media_list:
            if media["type"] == "image":
                await sync_to_async(PostImage.objects.create)(
                    post=post, image=media["path"], order=media["order"]
                )
            elif media["type"] == "video":
                post.video_url = media["path"]
                await sync_to_async(post.save)()

        return await self.get_post(post_id)

    async def count_posts_in_flow(self, flow_id: int) -> int:
        return await self.base_service.post_repo.count_posts_in_flow(flow_id=flow_id)

    async def create_post(
        self,
        flow_id: int,
        content: str,
        original_link: str,
        original_date: datetime,
        original_content: str,
        source_url: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        media_list: Optional[List[str]] = None,
    ) -> PostDTO:
        if not await self.flow_repo.exists(flow_id):
            raise PostNotFoundError(f"Flow with id {flow_id} not found")

        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        flow = await self.flow_repo.get_flow_by_id(flow_id)

        post = await self.base_service.post_repo.create_with_media(
            flow=flow,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_url=source_url,
            content=content,
            media_list=media_list,
        )
        return await sync_to_async(PostDTO.from_orm)(post)

    async def get_posts_by_flow_id(
        self, flow_id: int, status: PostStatus = None
    ) -> list[PostDTO]:
        posts = await self.base_service.post_repo.get_posts_by_flow_id(
            flow_id=flow_id, status=status
        )
        return posts

    @sync_to_async
    def get_channel_id(self, post_id: int) -> str:
        return (
            Post.objects.select_related("flow__channel")
            .get(id=post_id)
            .flow.channel.channel_id
        )
