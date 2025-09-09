
import asyncio
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Prefetch
from psycopg.errors import UniqueViolation
from PIL import Image, UnidentifiedImageError

from admin_panel.admin_panel.models import Flow, Post, PostImage
from bot.database.exceptions import PostNotFoundError
from bot.database.models import MediaType, PostDTO, PostStatus


class PostRepository:
    async def create(
        self,
        flow: Flow,
        content: str,
        source_url: Optional[str] = None,
        status: PostStatus = None,
        scheduled_time: Optional[datetime] = None,
        images: Optional[list[str]] = None,
        video_path: Optional[str] = None,
    ) -> Post:
        post = Post(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time,
        )
        await post.asave()

        if video_path:
            await self._save_video_from_path(post, video_path)

        if images:
            for image_path in images:
                await self._save_image_from_path(post, image_path)

        return post

    async def get(self, post_id: int) -> Post:
        try:
            query = Post.objects.select_related("flow").prefetch_related("images")
            return await query.aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found")

    async def update(self, post_id: int, **fields) -> Post:
        post = await self.get(post_id)
        for field, value in fields.items():
            setattr(post, field, value)
        await post.asave()
        return post

    async def delete(self, post_id: int) -> None:
        post = await self.get(post_id)
        await post.adelete()

    async def list(
        self,
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        is_published: Optional[bool] = None,
        scheduled_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Post]:
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
            post
            async for post in query.select_related("flow").order_by("-created_at")[
                offset : offset + limit
            ]
        ]

    async def exists(self, post_id: int) -> bool:
        return await Post.objects.filter(id=post_id).aexists()

    async def count_posts_in_flow(self, flow_id: int) -> int:
        return await Post.objects.filter(flow_id=flow_id).acount()

    async def _save_video_from_path(self, post: Post, video_path: str) -> None:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        filename = os.path.basename(video_path)
        destination = os.path.join(settings.MEDIA_ROOT, "videos", filename)
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        shutil.copy2(video_path, destination)
        post.video = os.path.relpath(destination, settings.MEDIA_ROOT)
        await post.asave()

    async def _save_image_from_path(self, post: Post, image_path: str) -> None:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            with Image.open(image_path) as img:
                img.verify()
        except (IOError, UnidentifiedImageError):
            raise ValueError(f"Invalid image file: {image_path}")

        filename = os.path.basename(image_path)
        destination = os.path.join(settings.MEDIA_ROOT, "images", filename)
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        shutil.copy2(image_path, destination)
        image_path_rel = os.path.relpath(destination, settings.MEDIA_ROOT)
        PostImage.objects.create(post=post, image=image_path_rel, order=post.images.count())

    async def update_media(
        self, post_id: int, media_file, filename: str, media_type: MediaType
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
