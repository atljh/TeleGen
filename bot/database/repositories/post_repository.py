import asyncio
import os
import logging
import shutil
import uuid
from django.conf import settings
from datetime import datetime
from typing import Optional, List
from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from django.db import IntegrityError, transaction
from psycopg.errors import UniqueViolation

from admin_panel.admin_panel.models import Post, Flow, PostImage
from bot.database.exceptions import PostNotFoundError
from bot.database.dtos.dtos import MediaType, PostDTO, PostImageDTO, PostStatus


class PostRepository:

    async def create(
        self,
        flow: Flow,
        content: str,
        source_url: Optional[str] = None,
        status: PostStatus = None,
        scheduled_time: Optional[datetime] = None,
        images: Optional[List[str]] = None,
        video_path: Optional[str] = None
    ) -> Post:
        post = Post(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
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
        original_link: str,
        original_date: datetime,
        source_url: str,
        source_id: str,
        scheduled_time: Optional[datetime] = None
    ) -> Optional[Post]:
        try:
            if await Post.objects.filter(source_id=source_id).aexists():
                logging.warning(f"Duplicate post skipped: {source_id}")
                return None

            @sync_to_async
            def _create_post_and_media():
                with transaction.atomic():
                    post = Post.objects.create(
                        flow=flow,
                        content=content,
                        original_link=original_link,
                        original_date=original_date,
                        source_url=source_url,
                        source_id=source_id,
                        status=PostStatus.DRAFT,
                        scheduled_time=scheduled_time
                    )
                    
                    for media in media_list:
                        media_type = media.get("type")
                        local_path = media.get("path")
                        if not local_path or not media_type:
                            continue

                        if media_type == MediaType.IMAGE.value:
                            self._save_image_sync(post, local_path)
                        elif media_type == MediaType.VIDEO.value:
                            self._save_video_sync(post, local_path)
                    
                    return post

            return await _create_post_and_media()

        except IntegrityError as e:
            if isinstance(e.__cause__, UniqueViolation):
                logging.warning(f"Duplicate post detected (source_id: {source_id})")
                return await Post.objects.filter(source_id=source_id).afirst()
            logging.error(f"Post creation error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    def _save_image_sync(self, post: Post, image_path: str) -> bool:
        try:
            ext = os.path.splitext(image_path)[1] or '.jpg'
            filename = f"{uuid.uuid4()}{ext}"
            
            permanent_path = os.path.join('images', filename)
            os.makedirs(os.path.dirname(permanent_path), exist_ok=True)
            shutil.copy(image_path, permanent_path)
            
            order = post.images.count()
            PostImage.objects.create(
                post=post,
                image=permanent_path,
                order=order
            )
            return True
        except Exception as e:
            logging.error(f"Failed to save image: {str(e)}")
            return False

    def _save_video_sync(self, post: Post, video_path: str) -> bool:
        try:
            ext = os.path.splitext(video_path)[1] or '.mp4'
            filename = f"{uuid.uuid4()}{ext}"
            
            permanent_path = os.path.join('videos', filename)
            os.makedirs(os.path.dirname(permanent_path), exist_ok=True)
            shutil.copy(video_path, permanent_path)
            
            post.video = permanent_path
            post.save()
            return True
        except Exception as e:
            logging.error(f"Failed to save video: {str(e)}")
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
        posts = Post.objects.filter(
            flow_id=flow_id,
            status__in=[Post.PUBLISHED, Post.DRAFT]
        )\
            .select_related('flow')\
            .prefetch_related(
                Prefetch('images', queryset=PostImage.objects.only('image', 'order').order_by('order'))
            )\
            .only(
                'id', 'content', 'source_url', 'publication_date',
                'status', 'created_at', 'scheduled_time',
                'video', 'flow__id', 'flow__name',
                'original_link', 'original_date', 'source_url'
            )\
            .order_by('-created_at')
        
        return [
            PostDTO.from_orm(post)
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
            status=PostStatus.SCHEDULED
        )