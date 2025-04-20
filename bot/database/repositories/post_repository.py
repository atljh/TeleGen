import os
import logging
import shutil
import uuid
from django.conf import settings
import requests
from datetime import datetime
import aiofiles
import aiohttp
from urllib.parse import urlparse
from django.core.files import File
from tempfile import NamedTemporaryFile
from typing import Optional, List, AsyncGenerator
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from admin_panel.admin_panel.models import Post, Flow
from bot.database.exceptions import PostNotFoundError, InvalidOperationError
from bot.database.dtos.dtos import MediaType


class PostRepository:

    async def create(
        self,
        flow: Flow,
        content: str,
        source_url: Optional[str] = None,
        is_draft: bool = True,
        scheduled_time: Optional[datetime] = None,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> Post:
        post = Post(
            flow=flow,
            content=content,
            source_url=source_url,
            is_draft=is_draft,
            scheduled_time=scheduled_time
        )

        await post.asave()

        if media_url and media_type:
            success = False
            if media_type == 'image':
                success = await self._download_and_save_media(
                    media_url,
                    post.image.save
                )
            elif media_type == 'video':
                success = await self._download_and_save_media(
                    media_url,
                    post.video.save
                )

            if success:
                await post.asave()
            else:
                logging.warning(f"Failed to save media for post {post.id}")


        return post


    # async def create_with_media(
    #     self,
    #     flow: Flow,
    #     content: str,
    #     media_list: list[dict],
    #     **kwargs
    # ) -> Post:
    #     post = Post(flow=flow, content=content, **kwargs)
    #     await sync_to_async(post.save)()
        
    #     for media in media_list[:1]:
    #         try:
    #             with open(media['path'], 'rb') as f:
    #                 file_obj = File(f)
                    
    #                 if media['type'] == 'image':
    #                     await sync_to_async(post.image.save)(
    #                         os.path.basename(media['path']),
    #                         file_obj
    #                     )
    #                 elif media['type'] == 'video':
    #                     await sync_to_async(post.video.save)(
    #                         os.path.basename(media['path']),
    #                         file_obj
    #                     )
                    
    #                 await sync_to_async(post.save)()
    #         except Exception as e:
    #             logging.error(f"Failed to save media: {str(e)}")
    #         finally:
    #             if os.path.exists(media['path']):
    #                 os.unlink(media['path'])
        
    #     return post

    async def create_with_media(
        self,
        flow: Flow,
        content: str,
        media_list: list[dict],
        **kwargs
    ) -> Post:
        """Создает пост с медиа, гарантируя сохранность файлов"""
        post = Post(flow=flow, content=content, **kwargs)
        await sync_to_async(post.save)()  # Сначала сохраняем пост

        if not media_list:
            return post

        # Обрабатываем только первый медиафайл (как в вашем оригинальном коде)
        media = media_list[0]
        if not media.get('path') or not os.path.exists(media['path']):
            logging.warning(f"Media file not found: {media.get('path')}")
            return post

        try:
            # Генерируем уникальное имя файла
            ext = os.path.splitext(media['path'])[1] or ('.jpg' if media['type'] == 'image' else '.mp4')
            filename = f"{uuid.uuid4()}{ext}"
            
            # Определяем конечный путь
            media_type_dir = 'images' if media['type'] == 'image' else 'videos'
            media_dir = os.path.join(settings.MEDIA_ROOT, 'posts', media_type_dir)
            
            # Создаем директорию, если не существует
            os.makedirs(media_dir, exist_ok=True)
            
            # Полный путь к новому файлу
            new_path = os.path.join(media_dir, filename)
            
            # Копируем файл (атомарная операция)
            shutil.copy2(media['path'], new_path)
            
            # Проверяем, что файл скопировался
            if not os.path.exists(new_path):
                raise FileNotFoundError(f"Failed to copy file to {new_path}")
            
            # Сохраняем относительный путь в БД
            relative_path = os.path.join('posts', media_type_dir, filename)
            if media['type'] == 'image':
                post.image.name = relative_path
            else:
                post.video.name = relative_path
                
            await sync_to_async(post.save)()
            
        except Exception as e:
            logging.error(f"Media processing failed: {str(e)}")
            if 'new_path' in locals() and os.path.exists(new_path):
                os.unlink(new_path)
        finally:
            if os.path.exists(media['path']):
                os.unlink(media['path'])
        
        return post

    async def _store_media_permanently(self, temp_path: str, media_type: str) -> str:
        media_dir = 'posts/images' if media_type == 'image' else 'posts/videos'
        os.makedirs(os.path.join(settings.MEDIA_ROOT, media_dir), exist_ok=True)
        
        filename = f"{uuid.uuid4()}{os.path.splitext(temp_path)[1]}"
        permanent_path = os.path.join(media_dir, filename)
        
        shutil.copy2(temp_path, os.path.join(settings.MEDIA_ROOT, permanent_path))
        return permanent_path

    async def _download_and_save_media(self, url: str, save_func) -> bool:
        try:
            if url.startswith(('http://', 'https://')):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            await sync_to_async(save_func)(
                                os.path.basename(url),
                                ContentFile(content)
                            )
                            return True
            else:
                async with aiofiles.open(url, mode='rb') as f:
                    content = await f.read()
                    await sync_to_async(save_func)(
                        os.path.basename(url),
                        ContentFile(content)
                    )
                    return True
        except Exception as e:
            logging.error(f"Error downloading/saving media: {str(e)}")
            return False

    async def get(self, post_id: int) -> Post:
        try:
            return await Post.objects.select_related('flow').aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found")

    async def update_media(
        self, 
        post_id: int, 
        media_file: bytes, 
        filename: str,
        media_type: MediaType
    ) -> Post:
        post = await self.get(post_id)
        
        if post.image:
            post.image.delete(save=False)
        if post.video:
            post.video.delete(save=False)
        
        if media_type == MediaType.IMAGE:
            post.image.save(filename, media_file, save=False)
        elif media_type == MediaType.VIDEO:
            post.video.save(filename, media_file, save=False)
        
        await post.asave()
        return post

    async def remove_media(self, post_id: int) -> Post:
        post = await self.get(post_id)
        if post.image:
            post.image.delete(save=False)
            post.image = None
        if post.video:
            post.video.delete(save=False)
            post.video = None
        await post.asave()
        return post

    async def get_posts_by_flow_id(self, flow_id: int) -> List[Post]:
        return [
            post async for post in 
            Post.objects.filter(flow_id=flow_id)
                .select_related('flow')
                .order_by('-created_at')
        ]

    async def exists(self, post_id: int) -> bool:
        return await Post.objects.filter(id=post_id).aexists()

    async def list(
        self,
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        is_published: Optional[bool] = None,
        scheduled_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        query = Post.objects.all()
        
        if flow_id:
            query = query.filter(flow_id=flow_id)
        if status:
            query = query.filter(status=status)
        if is_published is not None:
            query = query.filter(is_published=is_published)
        if scheduled_before:
            query = query.filter(scheduled_time__lte=scheduled_before)
            
        return [
            post async for post in 
            query.select_related('flow')
                .order_by('-created_at')
                [offset:offset+limit]
        ]

    async def count_posts_in_flow(self, flow_id: int) -> int:
        return await Post.objects.filter(flow_id=flow_id).acount()

    async def update(
        self,
        post_id: int,
        **fields
    ) -> Post:
        post = await self.get(post_id)
        for field, value in fields.items():
            setattr(post, field, value)
        await post.asave()
        return post

    async def delete(self, post_id: int) -> None:
        post = await self.get(post_id)
        await post.adelete()