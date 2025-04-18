import os
import logging
import requests
from datetime import datetime
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
        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")
        
        post = Post(
            flow=flow,
            content=content,
            source_url=source_url,
            is_draft=is_draft,
            scheduled_time=scheduled_time
        )

        if media_url and media_type:
            try:
                if media_type == 'image':
                    await self._save_image(post, media_url)
                elif media_type == 'video':
                    await self._save_video(post, media_url)
            except Exception as e:
                logging.error(f"Error saving media: {str(e)}")
                await post.asave()
                return post

        await post.asave()
        return post


    async def _save_image(self, post: Post, image_url: str):
        content = await self._download_file(image_url)
        if content:
            filename = os.path.basename(urlparse(image_url).path)
            await sync_to_async(post.image.save)(filename, ContentFile(content))

    async def _save_video(self, post: Post, video_url: str):
        content = await self._download_file(video_url)
        if content:
            filename = os.path.basename(urlparse(video_url).path)
            await sync_to_async(post.video.save)(filename, ContentFile(content))

    async def _download_file(self, url: str) -> Optional[bytes]:
        if url.startswith(('http://', 'https://')):
            try:
                response = await sync_to_async(requests.get)(url, stream=True)
                response.raise_for_status()
                return await sync_to_async(response.content)()
            except Exception as e:
                logging.error(f"Error downloading file {url}: {str(e)}")
                return None
        else:
            try:
                with open(url, 'rb') as f:
                    return await sync_to_async(f.read)()
            except Exception as e:
                logging.error(f"Error reading local file {url}: {str(e)}")
                return None


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