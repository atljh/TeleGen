import logging
import os

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from admin_panel.models import Post
from bot.database.exceptions import InvalidOperationError
from bot.database.models import PostDTO, PostStatus
from bot.services.post.base import PostBaseService

logger = logging.getLogger(__name__)


class PostPublishingService:
    def __init__(self, bot: Bot, post_base_service: PostBaseService):
        self.bot = bot
        self.post_service = post_base_service

    async def publish_post(self, post_id: int, channel_id: str) -> PostDTO:
        """
        Publish a post to a channel with transaction protection to prevent duplicates.
        Uses database-level locking to ensure only one publish operation succeeds.
        """
        @sync_to_async
        def check_and_lock_post():
            """Check post status and lock it to prevent concurrent modifications"""
            with transaction.atomic():
                # Lock the post row for update until transaction completes
                post_obj = Post.objects.select_for_update().get(id=post_id)

                # Check status while holding the lock
                if post_obj.status == PostStatus.PUBLISHED.value:
                    raise InvalidOperationError("Пост вже опублiкований!")

                # Return locked status - post will remain locked until transaction commits
                return True

        try:
            # Check and lock the post
            await check_and_lock_post()

            # Get post data using the existing service method (outside transaction)
            post = await self.post_service.get_post(post_id)

            # Send to channel
            await self._send_post_to_channel(post, channel_id)

            # Update status after successful send
            return await self.post_service.update_post(
                post_id=post_id,
                status=PostStatus.PUBLISHED,
                content=post.content,
                publication_date=timezone.now(),
                scheduled_time=None,
            )

        except InvalidOperationError:
            # Re-raise InvalidOperationError without wrapping
            raise
        except Exception as e:
            logger.error(f"Error publishing post {post_id}: {e}", exc_info=True)
            raise InvalidOperationError("Помилка публiкацiї") from e

    async def _send_post_to_channel(self, post: PostDTO, channel_id: str):
        caption = post.content[:1024] if len(post.content) > 1024 else post.content
        if post.images or post.videos:
            await self._send_media_group(post, channel_id, caption)
        else:
            await self._send_text_message(post, channel_id)

    async def _send_media_group(self, post: PostDTO, channel_id: str, caption: str):
        media_group = []
        caption_added = False

        for i, image in enumerate(post.images):
            # Add caption only to the first media item
            should_add_caption = not caption_added
            if image.url.startswith(("http://", "https://")):
                media = InputMediaPhoto(
                    media=image.url,
                    caption=caption if should_add_caption else None,
                    parse_mode="HTML",
                )
                media_group.append(media)
            else:
                media_path = os.path.join(settings.MEDIA_ROOT, image.url.lstrip("/"))
                media = InputMediaPhoto(
                    media=FSInputFile(media_path),
                    caption=caption if should_add_caption else None,
                    parse_mode="HTML",
                )
                media_group.append(media)

            if should_add_caption:
                caption_added = True

        for j, video in enumerate(post.videos):
            # Add caption only to the first media item (if not already added)
            should_add_caption = not caption_added
            media_path = os.path.join(settings.MEDIA_ROOT, video.url.lstrip("/"))
            media = InputMediaVideo(
                media=FSInputFile(media_path),
                caption=caption if should_add_caption else None,
                parse_mode="HTML",
            )
            media_group.append(media)

            if should_add_caption:
                caption_added = True

        if media_group:
            await self.bot.send_media_group(chat_id=channel_id, media=media_group)

    def _create_media_item(self, image, caption: str | None = None) -> InputMediaPhoto:
        if image.url.startswith(("http://", "https://")):
            return InputMediaPhoto(
                media=image.url, caption=caption, parse_mode=ParseMode.HTML
            )
        else:
            media_path = os.path.join(settings.MEDIA_ROOT, image.url.lstrip("/"))
            if os.path.exists(media_path):
                return InputMediaPhoto(
                    media=FSInputFile(media_path),
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )
            else:
                raise InvalidOperationError(f"Файл изображения не найден: {media_path}")

    async def _send_text_message(self, post: PostDTO, channel_id: str):
        if len(post.content) > 4096:
            chunks = [
                post.content[i : i + 4096] for i in range(0, len(post.content), 4096)
            ]
            for chunk in chunks:
                await self.bot.send_message(
                    chat_id=channel_id, text=chunk, parse_mode=ParseMode.HTML
                )
        else:
            await self.bot.send_message(
                chat_id=channel_id, text=post.content, parse_mode=ParseMode.HTML
            )
