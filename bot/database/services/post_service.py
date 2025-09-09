import logging
from datetime import datetime
from typing import Optional

from asgiref.sync import sync_to_async
from django.db import IntegrityError
from psycopg.errors import UniqueViolation

from admin_panel.admin_panel.models import Flow, Post, PostImage
from bot.database.models import MediaType, PostStatus
from bot.database.repositories.post_repository import PostRepository


class PostService:
    def __init__(self, post_repository: PostRepository):
        self.post_repository = post_repository

    async def create_with_media(
        self,
        flow: Flow,
        content: str,
        media_list: list[dict],
        original_link: str,
        original_date: datetime,
        source_url: str,
        source_id: str,
        original_content: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Optional[Post]:
        try:
            if await self._post_exists(source_id):
                return None

            return await self._create_post_with_media_transaction(
                flow=flow,
                content=content,
                media_list=media_list,
                original_link=original_link,
                original_date=original_date,
                original_content=original_content,
                source_url=source_url,
                source_id=source_id,
                scheduled_time=scheduled_time,
            )

        except IntegrityError as e:
            return await self._handle_integrity_error(e, source_id)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    async def _post_exists(self, source_id: str) -> bool:
        exists = await Post.objects.filter(source_id=source_id).aexists()
        if exists:
            logging.warning(f"Duplicate post skipped: {source_id}")
        return exists

    async def _create_post_with_media_transaction(
        self,
        flow: Flow,
        content: str,
        media_list: list[dict],
        original_link: str,
        original_date: datetime,
        source_url: str,
        source_id: str,
        original_content: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Post:
        @sync_to_async
        def _create_post_sync():
            return self._create_post(
                flow=flow,
                content=content,
                original_content=original_content,
                original_link=original_link,
                original_date=original_date,
                source_url=source_url,
                source_id=source_id,
                scheduled_time=scheduled_time,
            )

        post = await _create_post_sync()
        await self._process_media_list(post, media_list)
        return post

    def _create_post(
        self,
        flow: Flow,
        content: str,
        original_link: str,
        original_date: datetime,
        source_url: str,
        source_id: str,
        original_content: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Post:
        return Post.objects.create(
            flow=flow,
            content=content,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_url=source_url,
            source_id=source_id,
            status=PostStatus.DRAFT,
            scheduled_time=scheduled_time,
        )

    async def _process_media_list(self, post: Post, media_list: list[dict]):
        for media in media_list:
            try:
                await self._process_single_media(post, media)
            except Exception as e:
                logging.error(f"Failed to process media: {str(e)}")
                continue

    async def _process_single_media(self, post: Post, media: dict):
        media_type = media.get("type")
        local_path = media.get("path")

        if not local_path or not media_type:
            return

        permanent_path = await self._store_media_permanently(
            local_path, "images" if media_type == MediaType.IMAGE.value else "videos"
        )

        if media_type == MediaType.IMAGE.value:
            await sync_to_async(self._create_post_image)(post, permanent_path)
        elif media_type == MediaType.VIDEO.value:
            await sync_to_async(self._update_post_video)(post, permanent_path)

    def _create_post_image(self, post: Post, image_path: str):
        PostImage.objects.create(post=post, image=image_path, order=post.images.count())

    def _update_post_video(self, post: Post, video_path: str):
        post.video = video_path
        post.save()

    async def _handle_integrity_error(
        self, error: IntegrityError, source_id: str
    ) -> Optional[Post]:
        if isinstance(error.__cause__, UniqueViolation):
            logging.warning(f"Duplicate post detected (source_id: {source_id})")
            return await Post.objects.filter(source_id=source_id).afirst()
        logging.error(f"Database error: {str(error)}")
        raise error


    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> None:
        await sync_to_async(Post.objects.filter(id=post_id).update)(
            scheduled_time=scheduled_time, status=PostStatus.SCHEDULED
        )
