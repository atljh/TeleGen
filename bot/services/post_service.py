import os
import logging
from django.utils import timezone
from urllib.parse import unquote
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, URLInputFile
from datetime import datetime
from typing import Optional, List
from aiogram import Bot
from bot.database.dtos import PostDTO, FlowDTO
from bot.database.repositories import PostRepository, FlowRepository
from bot.database.exceptions import PostNotFoundError, InvalidOperationError
from django.conf import settings

class PostService:
    def __init__(
        self,
        post_repository: PostRepository,
        flow_repository: FlowRepository,
        bot: Bot,
        userbot_service
        ):
        self.post_repo = post_repository
        self.flow_repo = flow_repository
        self.bot = bot
        self.userbot_service = userbot_service


    async def generate_auto_posts(self, flow_id: int) -> list[PostDTO]:
        flow = await self.flow_repo.get(flow_id)
        generated_posts = []
        
        for _ in range(flow.flow_volume):
            content = await self._generate_post_content(flow)
            post = await self.create(
                flow_id=flow.id,
                content=content,
                status="draft",
            )
            generated_posts.append(post)
        
        return generated_posts
    
    async def _generate_post_content(self, flow: FlowDTO) -> str:
        return "Сгенерированный контент поста"

    async def create_post(
        self,
        flow_id: int,
        content: str,
        source_url: Optional[str] = None,
        status: str = "draft",
        scheduled_time: Optional[datetime] = None,
        media_url: Optional[str] = None
    ) -> PostDTO:

        if not await self.flow_repo.exists(flow_id):
            raise PostNotFoundError(f"Flow with id {flow_id} not found")
        
        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        post = await self.post_repo.create(
            flow_id=flow_id,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time,
            media_url=media_url
        )
        return PostDTO.from_orm(post)
    
    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        return PostDTO.from_orm(post)
    
    async def get_posts_by_flow_id(self, flow_id: int) -> list[PostDTO]:
        posts = await self.post_repo.get_posts_by_flow_id(flow_id=flow_id)
        return [PostDTO.from_orm(post) for post in posts]

    async def list_posts(
        self, 
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PostDTO]:
        posts = await self.post_repo.list(
            flow_id=flow_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [PostDTO.from_orm(post) for post in posts]

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
        return PostDTO.from_orm(updated_post)
    

    async def publish_post(self, post_id: int, channel_id: str) -> PostDTO:
        post = await self.get_post(post_id)

        if post.is_published:
            raise InvalidOperationError("Пост вже опублiкований!")
        
        try:
            caption = post.content[:1024] if len(post.content) > 1024 else post.content
            
            if post.media_type == 'image':
                if post.media_url.startswith(('http://', 'https://')):
                    photo = URLInputFile(post.media_url)
                    await self.bot.send_photo(
                        chat_id=channel_id,
                        photo=photo,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    relative_path = post.media_url.lstrip("/") if post.media_url else None
                    media_path = os.path.join(settings.BASE_DIR, relative_path) if relative_path else None
                    if media_path and os.path.exists(media_path):
                        photo = FSInputFile(media_path)
                        await self.bot.send_photo(
                            chat_id=channel_id,
                            photo=photo,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
            
            elif post.media_type == 'video':
                if post.media_url.startswith(('http://', 'https://')):
                    video = URLInputFile(post.media_url)
                    await self.bot.send_video(
                        chat_id=channel_id,
                        video=video,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    decoded_path = unquote(post.media_url)
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
                        raise InvalidOperationError("Файл не знайден")
            
            else:
                if len(post.content) > 4096:
                    chunks = [post.content[i:i+4096] for i in range(0, len(post.content), 4096)]
                    for chunk in chunks:
                        await self.bot.send_message(
                            chat_id=channel_id,
                            text=chunk
                        )
                else:
                    await self.bot.send_message(
                        chat_id=channel_id,
                        text=post.content
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
    
    async def update_post_image(
        self,
        post_id: int,
        image_url: str
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        await self.post_repo.update_image(post_id, image_url)
        updated_post = await self.post_repo.get(post_id)
        return PostDTO.from_orm(updated_post)

    async def update_post_video(
        self,
        post_id: int,
        video_url: str
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        await self.post_repo.update_video(post_id, video_url)
        updated_post = await self.post_repo.get(post_id)
        return PostDTO.from_orm(updated_post)

    async def remove_post_media(
        self,
        post_id: int
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        await self.post_repo.remove_media(post_id)
        updated_post = await self.post_repo.get(post_id)
        return PostDTO.from_orm(updated_post)

