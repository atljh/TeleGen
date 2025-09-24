import logging
from datetime import datetime

from django.utils import timezone

from admin_panel.models import Post
from bot.database.exceptions import PostNotFoundError
from bot.database.models import MediaType
from bot.database.models.post import PostStatus

logger = logging.getLogger(__name__)


class PostRepository:
    async def save(self, post: Post) -> Post:
        await post.asave()
        return post

    async def get(self, post_id: int) -> Post:
        try:
            query = Post.objects.select_related("flow").prefetch_related("images")
            return await query.aget(id=post_id)
        except Post.DoesNotExist as e:
            raise PostNotFoundError(f"Post with id={post_id} not found") from e

    async def update(self, post_id: int, **fields) -> Post:
        post = await self.get(post_id)
        for field, value in fields.items():
            setattr(post, field, value)
        await post.asave()
        return post

    async def delete(self, post_id: int) -> None:
        post = await self.get(post_id)
        await post.adelete()

    async def list(
        self,
        flow_id: int | None = None,
        status: str | None = None,
        is_published: bool | None = None,
        scheduled_before: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Post]:
        query = Post.objects.all()

        if flow_id:
            query = query.filter(flow_id=flow_id)
        if status:
            query = query.filter(status=status)
        if is_published is not None:
            query = query.filter(is_published=is_published)
        if scheduled_before:
            query = query.filter(scheduled_time__lte=scheduled_before)

        return [
            post
            async for post in query.select_related("flow")
            .prefetch_related("images")
            .order_by("-created_at")[offset : offset + limit]
        ]

    async def exists(self, post_id: int) -> bool:
        return await Post.objects.filter(id=post_id).aexists()

    async def exists_by_source_id(self, source_id: str) -> bool:
        return await Post.objects.filter(source_id=source_id).aexists()

    async def count_posts_in_flow(self, flow_id: int) -> int:
        return await Post.objects.filter(flow_id=flow_id).acount()

    async def update_media(
        self, post_id: int, media_file, filename: str, media_type: MediaType
    ) -> Post:
        post = await self.get(post_id)

        if post.image:
            post.image.delete(save=False)
        if post.video:
            post.video.delete(save=False)

        if media_type == MediaType.IMAGE:
            post.image.save(filename, media_file, save=False)
        elif media_type == MediaType.VIDEO:
            post.video.save(filename, media_file, save=False)

        await post.asave()
        return post

    async def remove_media(self, post_id: int) -> Post:
        post = await self.get(post_id)
        if post.image:
            post.image.delete(save=False)
            post.image = None
        if post.video:
            post.video.delete(save=False)
            post.video = None
        await post.asave()
        return post

    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> Post:
        post = await self.get(post_id)

        if timezone.is_naive(scheduled_time):
            scheduled_time = timezone.make_aware(scheduled_time)

        post.scheduled_time = scheduled_time
        post.status = PostStatus.SCHEDULED
        return await self.save(post)
