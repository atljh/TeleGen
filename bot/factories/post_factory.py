from datetime import datetime

from admin_panel.admin_panel.models import Flow, Post
from bot.database.models import PostStatus


class PostFactory:
    @staticmethod
    def create_post(
        flow: Flow,
        content: str,
        status: PostStatus | None = None,
        scheduled_time: datetime | None = None,
        source_url: str | None = None,
        original_link: str | None = None,
        original_date: datetime | None = None,
        source_id: str | None = None,
        original_content: str | None = None,
    ) -> Post:
        if original_content is None:
            original_content = ""

        post = Post(
            flow=flow,
            content=content,
            status=status or PostStatus.DRAFT,
            scheduled_time=scheduled_time,
            source_url=source_url,
            original_link=original_link,
            original_date=original_date,
            source_id=source_id,
            original_content=original_content,
        )

        return post
