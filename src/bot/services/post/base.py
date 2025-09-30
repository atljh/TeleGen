import logging
from datetime import datetime
from typing import Any

from asgiref.sync import sync_to_async
from django.utils import timezone

from admin_panel.models import Flow, Post, PostImage, PostVideo
from bot.database.exceptions import InvalidOperationError, PostNotFoundError
from bot.database.models import PostDTO, PostStatus
from bot.database.repositories import PostRepository
from bot.factories.post_factory import PostFactory
from bot.services.media_service import MediaService

logger = logging.getLogger(__name__)


class PostBaseService:
    def __init__(
        self, post_repository: PostRepository, media_service: MediaService
    ) -> None:
        self.post_repo = post_repository
        self.media_service = media_service

    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        return await PostDTO.from_orm_async(post)

    async def create_post(
        self,
        flow: Flow,
        content: str,
        original_content: str | None = None,
        original_link: str | None = None,
        original_date: datetime | None = None,
        source_url: str | None = None,
        media_list: list[dict] | None = None,
        status: PostStatus | None = None,
        scheduled_time: datetime | None = None,
        source_id: str | None = None,
    ) -> Post:
        if scheduled_time and scheduled_time < timezone.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        post = PostFactory.create_post(
            flow=flow,
            content=content,
            status=status or PostStatus.DRAFT,
            scheduled_time=scheduled_time,
            source_url=source_url,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_id=source_id,
        )

        post = await self.post_repo.save(post)
        await self.media_service.process_media_list(post, media_list)
        return post

    async def update_post(
        self,
        post_id: int,
        content: str | None = None,
        images: list[dict[str, Any]] | None = None,
        videos: list[dict[str, Any]] | None = None,
        publication_date: datetime | None = None,
        status: PostStatus | None = None,
        scheduled_time: datetime | None = None,
    ) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        if content is not None:
            post.content = content
        if publication_date is not None:
            post.publication_date = publication_date
        if status is not None:
            post.status = status
        if scheduled_time is not None:
            post.scheduled_time = scheduled_time

        if images is not None:
            await self._update_post_images(post, images)
        if videos is not None:
            await self._update_post_videos(post, videos)

        await post.asave()
        return await PostDTO.from_orm_async(post)

    async def _update_post_images(
        self, post: PostDTO, images: list[dict[str, Any]]
    ) -> None:
        await sync_to_async(lambda: post.images.all().delete())()
        for img_data in images:
            await sync_to_async(PostImage.objects.create)(
                post=post,
                image=img_data["file_path"],
                order=img_data["order"],
            )

    async def _update_post_videos(
        self, post: PostDTO, videos: list[dict[str, Any]]
    ) -> None:
        await sync_to_async(lambda: post.videos.all().delete())()
        for video_data in videos:
            await sync_to_async(PostVideo.objects.create)(
                post=post,
                video=video_data["file_path"],
                order=video_data["order"],
            )

    async def update_post_status(self, post_id: int, status: PostStatus) -> None:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        post.status = status
        await post.asave()

    async def delete_post(self, post_id: int) -> None:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")
        await self.post_repo.delete(post_id)

    async def get_all_posts_in_flow(
        self, flow_id: int, status: PostStatus
    ) -> list[PostDTO]:
        posts = await self.post_repo.list(flow_id=flow_id, status=status)
        posts = await sync_to_async(list)(posts)

        result: list[PostDTO] = []
        for post in posts:
            dto = await PostDTO.from_orm_async(post)
            result.append(dto)
        return result
