from datetime import datetime
from typing import Any

from asgiref.sync import sync_to_async
from admin_panel.admin_panel.models import Flow, Post, PostImage
from bot.database.exceptions import PostNotFoundError
from bot.database.models import PostDTO, PostStatus
from bot.database.repositories import PostRepository
from bot.factories.post_factory import PostFactory
from bot.services.media_service import MediaService


class PostBaseService:
    def __init__(
        self,
        post_repository: PostRepository,
        media_service: MediaService
    ) -> None:
        self.post_repo = post_repository
        self.media_service = media_service

    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        images = await sync_to_async(lambda: list(post.images.all().order_by("order")))()
        dto = PostDTO.from_orm(post)
        dto.images = images
        return dto

    async def create_post(
        self,
        flow: Flow,
        content: str,
        original_content: str,
        original_link: str,
        original_date: datetime,
        source_url: str | None = None,
        image_paths: list[str] | None = None,
        video_path: str | None = None,
        status: PostStatus | None = None,
        scheduled_time: datetime | None = None,
        source_id: str | None = None,
    ) -> PostDTO:

        stored_images = [self.media_service.save_image(p) for p in image_paths or []]
        stored_video = self.media_service.save_video(video_path) if video_path else None

        post = PostFactory.create_post(
            flow=flow,
            content=content,
            image_paths=stored_images,
            status=status,
            scheduled_time=scheduled_time,
            source_url=source_url,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_id=source_id,
        )

        if stored_video:
            post.video = stored_video

        post = await self.post_repo.save_with_images(post, stored_images)
        return PostDTO.from_orm(post)

    async def update_post(
        self,
        post_id: int,
        content: str | None = None,
        images: list[dict[str, Any]] | None = None,
        publication_date: datetime | None = None,
        status: PostStatus | None = None,
        video_url: str | None = None,
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
        if video_url is not None:
            post.video_url = video_url
        if scheduled_time is not None:
            post.scheduled_time = scheduled_time

        if images is not None:
            await self._update_post_images(post, images)

        await sync_to_async(post.save)()
        return PostDTO.from_orm(post)

    async def _update_post_images(self, post: Post, images: list[dict[str, Any]]) -> None:
        await sync_to_async(lambda: post.images.all().delete())()
        for img_data in images:
            await sync_to_async(PostImage.objects.create)(
                post=post,
                image=img_data["file_path"],
                order=img_data["order"],
            )

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
            images = await sync_to_async(lambda p=post: list(p.images.all().order_by("order")))()
            dto = PostDTO.from_orm(post)
            dto.images = images
            result.append(dto)
        return result
