import os
import logging
from datetime import datetime
from urllib.parse import unquote
from typing import Dict, Optional, List
from django.utils import timezone
from aiogram import Bot
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async
from django.conf import settings
from aiogram.types import FSInputFile, URLInputFile, InputMediaPhoto

from admin_panel.admin_panel.models import PostImage, Post
from bot.database.dtos import PostDTO, PostStatus
from bot.database.repositories import PostRepository, FlowRepository
from bot.database.exceptions import PostNotFoundError, InvalidOperationError

from bot.services.userbot_service import UserbotService
from bot.services.logger_service import TelegramLogger, get_logger

class PostService:
    def __init__(
        self,
        bot: Bot,
        web_service: 'WebService',
        userbot_service: UserbotService,
        post_repository: PostRepository,
        flow_repository: FlowRepository,
    ):
        self.post_repo = post_repository
        self.flow_repo = flow_repository
        self.bot = bot
        self.userbot_service = userbot_service
        self.web_service = web_service
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = get_logger()
        return self._logger

    async def get_all_posts_in_flow(self, flow_id: int) -> List[Post]:
        return await sync_to_async(list)(
            Post.objects.filter(flow_id=flow_id)
            .order_by('created_at')
        )

    async def get_oldest_posts(self, flow_id: int, limit: int) -> List[Post]:
        return await sync_to_async(list)(
            Post.objects.filter(flow_id=flow_id)
            .order_by('created_at')[:limit]
        )

    async def update_post_with_media(
        self,
        post_id: int,
        content: str,
        media_list: List[dict]
    ) -> PostDTO:
        post = await self.post_repo.get(post_id)
        
        post.content = content
        await sync_to_async(post.save)()
        
        await sync_to_async(lambda: post.images.all().delete())()
        
        for media in media_list:
            if media['type'] == 'image':
                await sync_to_async(PostImage.objects.create)(
                    post=post,
                    image=media['path'],
                    order=media['order']
                )
            elif media['type'] == 'video':
                post.video_url = media['path']
                await sync_to_async(post.save)()
        
        return await self.get_post(post_id)

    async def count_posts_in_flow(self, flow_id: int) -> int:
        return await self.post_repo.count_posts_in_flow(flow_id=flow_id)

    async def generate_auto_posts(self, flow_id: int) -> list[PostDTO]:

        flow = await self.flow_repo.get_flow_by_id(flow_id)
        if not flow:
            return []

        total_volume = flow.flow_volume
        sources = flow.sources

        count_telegram = sum(1 for item in sources if item['type'] == 'telegram')
        count_web = sum(1 for item in sources if item['type'] == 'web')

        total_sources = count_telegram + count_web
        if total_sources == 0:
            return []

        base_volume = total_volume // total_sources
        remainder = total_volume % total_sources

        userbot_volume = base_volume * count_telegram
        web_volume = base_volume * count_web

        if remainder:
            web_volume += remainder

        user = await sync_to_async(lambda: flow.channel.user)()

        logging.info(f"Generating posts: userbot={userbot_volume}, web={web_volume}, user: {user}")

        if self.logger:
            await self.logger.user_started_generation(
                user=user,
                flow_name=flow.name,
                flow_id=flow.id
            )

        userbot_posts = await self.userbot_service.get_last_posts(flow, userbot_volume)
        web_posts = await self.web_service.get_last_posts(flow, web_volume)
        combined_posts = userbot_posts + web_posts
        combined_posts.sort(key=lambda x: x.created_at, reverse=True)
        
        generated_posts = []

        for post_dto in combined_posts:
            try:
                if await Post.objects.filter(source_id=post_dto.source_id).aexists():
                    logging.info(f"Skipping duplicate post: {post_dto.source_id}")
                    continue

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
                    source_url=post_dto.source_url,
                    original_date=post_dto.original_date,
                    original_link=post_dto.original_link,
                    original_content=post_dto.original_content,
                    source_id=post_dto.source_id,
                    media_list=media_list
                )
                
                if post:
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
        original_link: str,
        original_date: datetime,
        original_content: str,
        source_url: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        media_list: Optional[List[str]] = None,
    ) -> PostDTO:
        if not await self.flow_repo.exists(flow_id):
            raise PostNotFoundError(f"Flow with id {flow_id} not found")
        
        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        flow = await self.flow_repo.get_flow_by_id(flow_id)

        post = await self.post_repo.create_with_media(
            flow=flow,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_url=source_url,
            content=content,
            media_list=media_list,
        )
        return await sync_to_async(PostDTO.from_orm)(post)

    async def publish_post(self, post_id: int, channel_id: str) -> PostDTO:
        post = await self.get_post(post_id)
        if post.status == PostStatus.PUBLISHED:
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
                status=PostStatus.PUBLISHED,
                content=post.content,
                publication_date=timezone.now(),
                scheduled_time=None
            )
            
        except Exception as e:
            raise InvalidOperationError(f"Помилка публiкацiї: {str(e)}")

    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)

        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        
        images_qs = await sync_to_async(lambda: list(post.images.all().order_by('order')))()
        return PostDTO.from_orm(post, images=images_qs)
    
    async def get_posts_by_flow_id(self, flow_id: int, status: PostStatus = None) -> list[PostDTO]:
        posts = await self.post_repo.get_posts_by_flow_id(flow_id=flow_id, status=status)
        return posts

    async def update_post(
        self,
        post_id: int,
        content: Optional[str] = None,
        images: Optional[List[dict]] = None,
        publication_date: Optional[datetime] = None,
        status: Optional[PostStatus] = None,
        video_url: Optional[str] = None,
        **kwargs
    ) -> PostDTO:
        post = await self.post_repo.get(post_id)
        
        if content is not None:
            post.content = content
        if publication_date:
            post.publication_date = publication_date
        if status:
            post.status = status
        if images is not None:
            await sync_to_async(lambda: post.images.all().delete())()
            
            for img_data in images:
                await sync_to_async(PostImage.objects.create)(
                    post=post,
                    image=img_data["file_path"],
                    order=img_data["order"]
                )
        
        if video_url is not None:
            post.video_url = video_url
        
        await sync_to_async(post.save)()
        
        return await self.get_post(post_id)
        
    async def delete_post(self, post_id: int) -> None:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")
        await self.post_repo.delete(post_id)

    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> PostDTO:
        now = datetime.now(scheduled_time.tzinfo)
        
        if scheduled_time < now:
            raise InvalidOperationError("Не можна запланувати пост у минулому")
            
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
            
        await self.post_repo.schedule_post(post_id, scheduled_time)
        return await self.get_post(post_id)

    @sync_to_async
    def get_channel_id(self, post_id: int) -> str:
        return Post.objects.select_related("flow__channel").get(id=post_id).flow.channel.channel_id

    async def publish_scheduled_posts(self) -> List[PostDTO]:
        now = datetime.now()
        posts = await sync_to_async(list)(
            Post.objects.filter(
                status=PostStatus.SCHEDULED,
                scheduled_time__isnull=False,
                scheduled_time__lte=now
            )
        )
        
        published = []
        for post in posts:
            try:
                channel_id = await self.get_channel_id(post.id)
                result = await self.publish_post(post.id, channel_id)
                published.append(result)
            except Exception as e:
                logging.error(f"Failed to publish scheduled post {post.id}: {e}")
                
        return published
    