import os
import shutil
import logging
from typing import Optional
from datetime import datetime

from django.conf import settings
from PIL import Image, UnidentifiedImageError

from admin_panel.admin_panel.models import Flow, Post, PostImage
from bot.database.models import PostStatus

logger = logging.getLogger(__name__)


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
        return PostImage(
            post=post,
            image=image_path,
            order=order
        )

    @staticmethod
    def validate_image(image_path: str) -> None:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            with Image.open(image_path) as img:
                img.verify()
        except (IOError, UnidentifiedImageError) as e:
            raise ValueError(f"Invalid image file: {image_path} - {str(e)}")

    @staticmethod
    def copy_media_to_storage(source_path: str, media_type: str) -> str:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"File not found: {source_path}")

        if media_type == "image":
            target_dir = os.path.join(settings.MEDIA_ROOT, "images")
        elif media_type == "video":
            target_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        else:
            raise ValueError(f"Unknown media type: {media_type}")

        os.makedirs(target_dir, exist_ok=True)

        filename = f"{os.path.splitext(os.path.basename(source_path))[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(source_path)[1]}"
        destination = os.path.join(target_dir, filename)

        shutil.copy2(source_path, destination)

        return os.path.relpath(destination, settings.MEDIA_ROOT)

    @staticmethod
    def create_post_with_media(
        flow: Flow,
        content: str,
        image_paths: Optional[list[str]] = None,
        video_path: Optional[str] = None,
        **kwargs
    ) -> Post:

        post = PostFactory.create_post(flow=flow, content=content, **kwargs)
        
        if video_path:
            try:
                post.video = PostFactory.copy_media_to_storage(video_path, "video")
            except Exception as e:
                logger.error(f"Failed to process video: {str(e)}")

        if image_paths:
            for image_path in image_paths:
                try:
                    PostFactory.validate_image(image_path)
                    PostFactory.copy_media_to_storage(image_path, "image")
                except Exception as e:
                    logger.error(f"Failed to process image {image_path}: {str(e)}")

        return post