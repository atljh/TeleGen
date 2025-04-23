from datetime import datetime
import os
import random
import logging
from urllib.parse import unquote
from typing import Optional, List
from django.utils import timezone
from aiogram import Bot
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async
from aiogram.types import FSInputFile, URLInputFile, InputMediaPhoto, InputMediaVideo
from bot.database.dtos import PostDTO, FlowDTO, PostImageDTO
from bot.database.dtos.dtos import ContentLength
from bot.database.repositories import PostRepository, FlowRepository
from bot.database.exceptions import PostNotFoundError, InvalidOperationError
from django.conf import settings

from bot.services.userbot_service import UserbotService

class PostService:
    def __init__(
        self,
        post_repository: PostRepository,
        flow_repository: FlowRepository,
        bot: Bot,
        userbot_service: UserbotService
    ):
        self.post_repo = post_repository
        self.flow_repo = flow_repository
        self.bot = bot
        self.userbot_service = userbot_service

    async def count_posts_in_flow(self, flow_id: int) -> int:
        return await self.post_repo.count_posts_in_flow(flow_id=flow_id)

    async def generate_auto_posts(self, flow_id: int) -> list[PostDTO]:
        flow = await self.flow_repo.get_flow_by_id(flow_id)
        if not flow:
            return []

        posts_dto = await self.userbot_service.get_last_posts(flow)

        generated_posts = []
        for post_dto in posts_dto:
            try:
                media_list = [
                    {'path': img.url, 'type': 'image', 'order': img.order}
                    for img in post_dto.images
                ]
                if post_dto.video_url:
                    media_list.append({
                        'path': post_dto.video_url,
                        'type': 'video',
                        'order': len(post_dto.images)
                    })
                post = await self.post_repo.create_with_media(
                    flow=flow,
                    content=post_dto.content,
                    media_list=media_list,
                    is_draft=True
                )
                
                db_post_dto = await sync_to_async(PostDTO.from_orm)(post)
                generated_posts.append(db_post_dto)

            except Exception as e:
                logging.error(f"Post creation failed: {str(e)}")
                continue

        return generated_posts

    async def create_post(
        self,
        flow_id: int,
        content: str,
        source_url: Optional[str] = None,
        is_draft: bool = True,
        scheduled_time: Optional[datetime] = None,
        image_urls: Optional[List[str]] = None,
        video_url: Optional[str] = None
    ) -> PostDTO:
        if not await self.flow_repo.exists(flow_id):
            raise PostNotFoundError(f"Flow with id {flow_id} not found")
        
        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        flow = await self.flow_repo.get_flow_by_id(flow_id)

        post = await self.post_repo.create(
            flow=flow,
            content=content,
            source_url=source_url,
            is_draft=is_draft,
            scheduled_time=scheduled_time,
            images=image_urls,
            video_url=video_url
        )
        return PostDTO.from_orm(post)

    async def publish_post(self, post_id: int, channel_id: str) -> PostDTO:
        post = await self.get_post(post_id)

        if post.is_published:
            raise InvalidOperationError("Пост вже опублiкований!")
        
        try:
            caption = post.content[:1024] if len(post.content) > 1024 else post.content
            
            if post.images:
                media_group = []
                for i, image in enumerate(post.images):
                    if i == 0:
                        if image.url.startswith(('http://', 'https://')):
                            media = InputMediaPhoto(media=image.url, caption=caption, parse_mode=ParseMode.HTML)
                        else:
                            media_path = os.path.join(settings.BASE_DIR, image.url.lstrip("/"))
                            if os.path.exists(media_path):
                                media = InputMediaPhoto(media=FSInputFile(media_path), caption=caption, parse_mode=ParseMode.HTML)
                            else:
                                raise InvalidOperationError(f"Файл изображения не найден: {image.url}")
                    else:
                        if image.url.startswith(('http://', 'https://')):
                            media = InputMediaPhoto(media=image.url)
                        else:
                            media_path = os.path.join(settings.BASE_DIR, image.url.lstrip("/"))
                            if os.path.exists(media_path):
                                media = InputMediaPhoto(media=FSInputFile(media_path))
                            else:
                                raise InvalidOperationError(f"Файл изображения не найден: {image.url}")
                    
                    media_group.append(media)
                
                await self.bot.send_media_group(chat_id=channel_id, media=media_group)
            
            elif post.video_url:
                if post.video_url.startswith(('http://', 'https://')):
                    video = URLInputFile(post.video_url)
                    await self.bot.send_video(
                        chat_id=channel_id,
                        video=video,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    decoded_path = unquote(post.video_url)
                    relative_path = decoded_path.lstrip("/")
                    media_path = os.path.join(settings.BASE_DIR, relative_path)
                    if media_path and os.path.exists(media_path):
                        video = FSInputFile(media_path)
                        await self.bot.send_video(
                            chat_id=channel_id,
                            video=video,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        raise InvalidOperationError("Файл видео не найден")
            
            else:
                if len(post.content) > 4096:
                    chunks = [post.content[i:i+4096] for i in range(0, len(post.content), 4096)]
                    for chunk in chunks:
                        await self.bot.send_message(
                            chat_id=channel_id,
                            text=chunk,
                            parse_mode=ParseMode.HTML
                        )
                else:
                    await self.bot.send_message(
                        chat_id=channel_id,
                        text=post.content,
                        parse_mode=ParseMode.HTML
                    )
            
            return await self.update_post(
                post_id=post_id,
                is_published=True,
                content=post.content,
                publication_date=timezone.now(),
                scheduled_time=None
            )
            
        except Exception as e:
            raise InvalidOperationError(f"Помилка публiкацiї: {str(e)}")

    async def update_post_images(
        self,
        post_id: int,
        image_urls: List[str]
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        await self.post_repo.update_images(post_id, image_urls)
        updated_post = await self.post_repo.get(post_id)
        return PostDTO.from_orm(updated_post)

    async def add_post_image(
        self,
        post_id: int,
        image_url: str
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        await self.post_repo.add_image(post_id, image_url)
        updated_post = await self.post_repo.get(post_id)
        return PostDTO.from_orm(updated_post)

    async def remove_post_image(
        self,
        post_id: int,
        image_id: int
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        await self.post_repo.remove_image(post_id, image_id)
        updated_post = await self.post_repo.get(post_id)
        return PostDTO.from_orm(updated_post)

    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)

        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        
        images_qs = await sync_to_async(lambda: list(post.images.all().order_by('order')))()
        return PostDTO.from_orm(post, images=images_qs)
    
    async def get_posts_by_flow_id(self, flow_id: int) -> list[PostDTO]:
        posts = await self.post_repo.get_posts_by_flow_id(flow_id=flow_id)
        return posts

    async def update_post(
        self,
        post_id: int,
        content: Optional[str] = None,
        status: Optional[str] = None,
        source_url: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        publication_date: Optional[datetime] = None,
        is_published: Optional[bool] = None
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        updated_post = await self.post_repo.update(
            post_id=post_id,
            content=content,
            status=status,
            source_url=source_url,
            scheduled_time=scheduled_time,
            publication_date=publication_date,
            is_published=is_published
        )
        images_qs = await sync_to_async(lambda: list(updated_post.images.all().order_by('order')))()
        return PostDTO.from_orm(updated_post, images=images_qs)

    async def delete_post(self, post_id: int) -> None:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")
        await self.post_repo.delete(post_id)

    async def get_scheduled_posts(self) -> List[PostDTO]:
        posts = await self.post_repo.list(
            status="scheduled",
            scheduled_time_lt=datetime.now()
        )
        return [PostDTO.from_orm(post) for post in posts]