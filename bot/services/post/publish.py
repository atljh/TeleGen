import os

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from django.conf import settings
from django.utils import timezone

from bot.database.exceptions import InvalidOperationError
from bot.database.models import PostDTO, PostStatus
from bot.services.post.base import PostBaseService


class PostPublishingService:
    def __init__(self, bot: Bot, post_base_service: PostBaseService):
        self.bot = bot
        self.post_service = post_base_service

    async def publish_post(self, post_id: int, channel_id: str) -> PostDTO:
        post = await self.post_service.get_post(post_id)
        if post.status == PostStatus.PUBLISHED:
            raise InvalidOperationError("Пост вже опублiкований!")

        try:
            await self._send_post_to_channel(post, channel_id)

            return await self.post_service.update_post(
                post_id=post_id,
                status=PostStatus.PUBLISHED,
                content=post.content,
                publication_date=timezone.now(),
                scheduled_time=None,
            )

        except Exception as e:
            raise InvalidOperationError(f"Помилка публiкацiї: {e!s}") from e

    async def _send_post_to_channel(self, post: PostDTO, channel_id: str):
        caption = post.content[:1024] if len(post.content) > 1024 else post.content

        if post.images or post.videos:
            await self._send_media_group(post, channel_id, caption)
        else:
            await self._send_text_message(post, channel_id)

    async def _send_media_group(self, post: PostDTO, channel_id: str, caption: str):
        media_group = []

        for i, image in enumerate(post.images):
            media = InputMediaPhoto(
                media=image,
                caption=caption if i == 0 and not post.videos else None,
                parse_mode="HTML",
            )
            media_group.append(media)

        for j, video in enumerate(post.videos):
            media = InputMediaVideo(
                media=video,
                caption=caption if j == 0 and not post.images else None,
                parse_mode="HTML",
            )
            media_group.append(media)

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
