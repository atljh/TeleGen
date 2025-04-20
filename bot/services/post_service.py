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
from aiogram.types import FSInputFile, URLInputFile
from bot.database.dtos import PostDTO, FlowDTO
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

        posts_data = await self.userbot_service.get_last_posts(flow.sources)

        generated_posts = []
        for post_data in posts_data:
            try:
                media_list = post_data.get('media', [])

                post = await self.post_repo.create_with_media(
                    flow=flow,
                    content=post_data['text'],
                    media_list=media_list,
                    is_draft=True
                )
                generated_posts.append(PostDTO.from_orm(post))

            except Exception as e:
                logging.error(f"Post creation failed: {str(e)}")

        return generated_posts


    async def _get_last_posts_content(self, flow: FlowDTO, needed_count: int) -> list[str]:
        try:
            posts_limit = needed_count * 2
            
            sources_content = await self.userbot_service.get_last_posts(
                flow.sources,
                posts_limit=posts_limit
            )
            
            if not sources_content:
                logging.warning(f"No content found for flow {flow.id}")
                return []
                
            return sources_content
        except Exception as e:
            logging.error(f"Error getting last posts for flow {flow.id}: {str(e)}")
            return []

    async def _generate_post_content(self, flow: FlowDTO) -> str:
        try:
            sources_content = await self.userbot_service.get_last_posts(
                flow.sources,
                posts_limit=10 
            )
            
            if not sources_content:
                logging.warning(f"No content found for flow {flow.id}")
                return "Контент не найден"
            
            selected_content = sources_content[:flow.flow_volume]
            
            return self._process_content(
                raw_content=selected_content,
                theme=flow.theme,
                content_length=flow.content_length,
                use_emojis=flow.use_emojis,
                use_premium_emojis=flow.use_premium_emojis,
                title_highlight=flow.title_highlight,
                cta=flow.cta,
                signature=flow.signature
            )
        except Exception as e:
            logging.error(f"Content generation error for flow {flow.id}: {str(e)}")
            return "Ошибка генерации контента"

    def _process_content(
        self,
        raw_content: List[str],
        theme: str,
        content_length: ContentLength,
        use_emojis: bool,
        use_premium_emojis: bool,
        title_highlight: bool,
        cta: bool,
        signature: Optional[str]
    ) -> str:
        selected_content = self._select_content_by_length(raw_content, content_length)
        
        formatted_content = []
        for item in selected_content:
            if use_emojis:
                item = self._add_emojis(item, use_premium_emojis)
            
            if title_highlight:
                item = self._highlight_titles(item)
            
            formatted_content.append(item)
        
        main_content = "\n\n".join(formatted_content)
        
        if theme:
            main_content = f"Тема: {theme}\n\n{main_content}"
        
        if cta:
            main_content += "\n\nЩо ви думаєте з цього приводу?"
        
        if signature:
            main_content += f"\n\n{signature}"
        
        return main_content

    def _select_content_by_length(self, content: List[str], length: ContentLength) -> List[str]:
        if length == ContentLength.SHORT:
            return [random.choice(content)] if content else []
        elif length == ContentLength.MEDIUM:
            return content[:2] if len(content) >= 2 else content
        else:
            return content[:4] if len(content) >= 4 else content

    def _add_emojis(self, text: str, premium: bool) -> str:
        emoji_dict = {
            '!': '❗',
            '?': '❓',
            'important': '⚠️',
            'news': '📰',
            'update': '🔄'
        }
        
        if premium:
            emoji_dict.update({
                '!': '‼️',
                '?': '❔',
                'important': '🚨',
                'news': '📻',
                'update': '💫'
            })
        
        for word, emoji in emoji_dict.items():
            if word in text.lower():
                text = f"{emoji} {text}"
                break
        
        return text

    def _highlight_titles(self, text: str) -> str:
        lines = text.split('\n')
        if len(lines) > 1:
            lines[0] = f"<b>{lines[0]}</b>"
        return '\n'.join(lines)

    async def create_post(
        self,
        flow_id: int,
        content: str,
        source_url: Optional[str] = None,
        is_draft: bool = True,
        scheduled_time: Optional[datetime] = None,
        media_url: Optional[str] = None
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


    async def _cleanup_temp_files(self, file_paths: list[str]):
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as e:
                    logging.warning(f"Could not delete temp file {path}: {str(e)}")