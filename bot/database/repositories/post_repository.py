import asyncio
import os
import logging
import shutil
import uuid
from django.conf import settings
from datetime import datetime
from typing import Optional, List
from asgiref.sync import sync_to_async
from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from aiogram_dialog.api.entities import MediaAttachment
from admin_panel.admin_panel.models import Post, Flow, PostImage
from bot.database.exceptions import PostNotFoundError
from bot.database.dtos.dtos import MediaType, PostDTO, PostImageDTO


class PostRepository:

    async def create(
        self,
        flow: Flow,
        content: str,
        source_url: Optional[str] = None,
        is_draft: bool = True,
        scheduled_time: Optional[datetime] = None,
        images: Optional[List[str]] = None,
        video_path: Optional[str] = None
    ) -> Post:
        post = Post(
            flow=flow,
            content=content,
            source_url=source_url,
            is_draft=is_draft,
            scheduled_time=scheduled_time
        )
        await post.asave()

        if video_path:
            await self._save_video_from_path(post, video_path)

        if images:
            for image_path in images:
                await self._save_image_from_path(post, image_path)

        return post

    async def create_with_media(
        self,
        flow: Flow,
        content: str,
        media_list: List[dict],
        is_draft: bool = True,
        scheduled_time: Optional[datetime] = None
    ) -> Post:
        post = Post(
            flow=flow,
            content=content,
            is_draft=is_draft,
            scheduled_time=scheduled_time
        )
        await post.asave()

        for media in media_list:
            media_type = media.get("type")
            local_path = media.get("path")
            if not local_path or not media_type:
                continue

            if media_type == MediaType.IMAGE.value:
                await self._save_image_from_path(post, local_path)
            elif media_type == MediaType.VIDEO.value:
                await self._save_video_from_path(post, local_path)

        return post

    async def _save_image_from_path(self, post: Post, image_path: str) -> bool:
        try:
            ext = os.path.splitext(image_path)[1] or '.jpg'
            filename = f"{uuid.uuid4()}{ext}"
            permanent_path = await self._store_media_permanently(image_path, 'images')
            
            order = await sync_to_async(lambda: post.images.count())()
            post_image = PostImage(
                post=post,
                image=permanent_path,
                order=order
            )
            await sync_to_async(post_image.save)()
            return True
        except Exception as e:
            logging.error(f"Failed to save image from path: {str(e)}")
            return False

    async def _save_video_from_path(self, post: Post, video_path: str) -> bool:
        try:
            ext = os.path.splitext(video_path)[1] or '.mp4'
            filename = f"{uuid.uuid4()}{ext}"
            permanent_path = await self._store_media_permanently(video_path, 'videos')
            
            post.video.name = permanent_path
            await post.asave()
            return True
        except Exception as e:
            logging.error(f"Failed to save video from path: {str(e)}")
            return False

    async def _store_media_permanently(self, temp_path: str, media_type: str) -> str:
        media_dir = 'posts/images' if media_type == 'images' else 'posts/videos'
        os.makedirs(os.path.join(settings.MEDIA_ROOT, media_dir), exist_ok=True)
        
        ext = os.path.splitext(temp_path)[1]
        filename = f"{uuid.uuid4()}{ext}"
        permanent_path = os.path.join(media_dir, filename)
        
        shutil.copy2(temp_path, os.path.join(settings.MEDIA_ROOT, permanent_path))
        return permanent_path

    async def get(self, post_id: int) -> Post:
        try:
            query = Post.objects.select_related('flow').prefetch_related('images')
            return await query.aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found")

    async def update_media(
        self, 
        post_id: int, 
        media_file, 
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

    async def get_posts_by_flow_id(self, flow_id: int) -> List[PostDTO]:
        posts = await self._fetch_posts_from_db(flow_id)
        await self._preload_media_for_posts(posts)
        return posts
    
    @sync_to_async
    def _fetch_posts_from_db(self, flow_id: int) -> List[PostDTO]:
        posts = Post.objects.filter(flow_id=flow_id)\
            .select_related('flow')\
            .prefetch_related(
                Prefetch('images', queryset=PostImage.objects.only('image', 'order').order_by('order'))
            )\
            .only(
                'id', 'content', 'source_url', 'publication_date',
                'is_published', 'is_draft', 'created_at', 'scheduled_time',
                'video', 'flow__id', 'flow__name'
            )\
            .order_by('-created_at')
        
        return [
            PostDTO(
                id=post.id,
                flow_id=post.flow_id,
                content=post.content,
                source_url=post.source_url,
                publication_date=post.publication_date,
                is_published=post.is_published,
                is_draft=post.is_draft,
                created_at=post.created_at,
                scheduled_time=post.scheduled_time,
                images=[
                    PostImageDTO(
                        url=image.image.url,
                        order=image.order
                    ) for image in post.images.all()
                ],
                video_url=post.video.url if post.video else None
            )
            for post in posts
        ]
    
    async def _preload_media_for_posts(self, posts: List[PostDTO]):
        tasks = []
        
        for post in posts[:3]:
            if post.images:
                tasks.append(self._preload_media(post.images[0].url, 'image'))
            elif post.video_url:
                tasks.append(self._preload_media(post.video_url, 'video'))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _preload_media(self, media_url: str, media_type: str) -> bool:
        try:
            if not media_url:
                return False
                
            media_path = os.path.join(
                settings.MEDIA_ROOT, 
                media_url.replace(settings.MEDIA_URL, '').lstrip('/')
            )
            
            if os.path.exists(media_path):
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error preloading media {media_url}: {str(e)}")
            return False

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

    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> None:
        await sync_to_async(Post.objects.filter(id=post_id).update)(
            scheduled_time=scheduled_time,
            is_draft=True
        )