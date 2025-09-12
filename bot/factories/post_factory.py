from datetime import datetime
from typing import Optional
from admin_panel.admin_panel.models import Flow, Post, PostImage
from bot.database.models import PostStatus


class PostFactory:
    @staticmethod
    def create_post(
        flow: Flow,
        content: str,
        source_url: Optional[str] = None,
        status: PostStatus = None,
        scheduled_time: Optional[datetime] = None,
        original_link: Optional[str] = None,
        original_date: Optional[datetime] = None,
        source_id: Optional[str] = None,
        original_content: Optional[str] = None,
    ) -> Post:
        return Post(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status or PostStatus.DRAFT,
            scheduled_time=scheduled_time,
            original_link=original_link,
            original_date=original_date,
            source_id=source_id,
            original_content=original_content,
        )

    @staticmethod
    def create_post_image(post: Post, image_path: str, order: int = 0) -> PostImage:
        return PostImage(post=post, image=image_path, order=order)

    @staticmethod
    def create_post_with_images(
        flow: Flow,
        content: str,
        image_paths: list[str],
        **kwargs
    ) -> Post:
        post = PostFactory.create_post(flow, content, **kwargs)
        post.images = [
            PostFactory.create_post_image(post, path, i)
            for i, path in enumerate(image_paths)
        ]
        return post
