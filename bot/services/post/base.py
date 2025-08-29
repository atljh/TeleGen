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
from bot.database.models import PostDTO, PostStatus
from bot.database.repositories import PostRepository, FlowRepository
from bot.database.exceptions import PostNotFoundError, InvalidOperationError

class PostBaseService:
    
    def __init__(self, post_repository: PostRepository):
        self.post_repo = post_repository

    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        
        images_qs = await sync_to_async(lambda: list(post.images.all().order_by('order')))()
        return PostDTO.from_orm(post, images=images_qs)

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
            await self._update_post_images(post, images)
        
        if video_url is not None:
            post.video_url = video_url
        
        await sync_to_async(post.save)()
        return await self.get_post(post_id)

    async def _update_post_images(self, post: Post, images: List[dict]):
        """Обновляет изображения поста"""
        await sync_to_async(lambda: post.images.all().delete())()
        
        for img_data in images:
            await sync_to_async(PostImage.objects.create)(
                post=post,
                image=img_data["file_path"],
                order=img_data["order"]
            )

    async def delete_post(self, post_id: int) -> None:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")
        await self.post_repo.delete(post_id)