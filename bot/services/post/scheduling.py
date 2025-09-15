import logging
from datetime import datetime
from django.utils import timezone
import pytz

from asgiref.sync import sync_to_async

from admin_panel.admin_panel.models import Post
from bot.database.exceptions import InvalidOperationError, PostNotFoundError
from bot.database.models import PostDTO, PostStatus
from bot.services.post.base import PostBaseService
from bot.services.post.publish import PostPublishingService


class PostSchedulingService:
    def __init__(
        self,
        post_base_service: PostBaseService,
        publishing_service: PostPublishingService,
    ):
        self.post_service = post_base_service
        self.publishing_service = publishing_service

    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> PostDTO:


        if timezone.is_naive(scheduled_time):
            ukraine_tz = pytz.timezone('Europe/Kiev')
            scheduled_time = ukraine_tz.localize(scheduled_time)

        scheduled_time_utc = scheduled_time.astimezone(pytz.UTC)
        current_time_utc = timezone.now()

        if scheduled_time_utc < current_time_utc:
            raise InvalidOperationError("Scheduled time cannot be in the past")

        post = await self.post_service.get_post(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        await self.post_service.post_repo.schedule_post(post_id, scheduled_time_utc)
        return await self.post_service.get_post(post_id)

    @sync_to_async
    def get_channel_id(self, post_id: int) -> str:
        return (
            Post.objects.select_related("flow__channel")
            .get(id=post_id)
            .flow.channel.channel_id
        )

    async def publish_scheduled_posts(self) -> list[PostDTO]:
        now = datetime.now()
        posts = await sync_to_async(list)(
            Post.objects.filter(
                status=PostStatus.SCHEDULED,
                scheduled_time__isnull=False,
                scheduled_time__lte=now,
            )
        )

        published = []
        for post in posts:
            try:
                channel_id = await self.get_channel_id(post.id)
                result = await self.publishing_service.publish_post(post.id, channel_id)
                published.append(result)
            except Exception as e:
                logging.error(f"Failed to publish scheduled post {post.id}: {e}")

        return published
