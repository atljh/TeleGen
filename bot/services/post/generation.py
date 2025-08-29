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
from bot.services.post import PostBaseService
from bot.services.userbot_service import UserbotService
from bot.services.web.web_service import WebService


class PostGenerationService:
    
    def __init__(
        self,
        userbot_service: UserbotService,
        web_service: WebService,
        flow_repository: FlowRepository,
        post_base_service: PostBaseService
    ):
        self.userbot_service = userbot_service
        self.web_service = web_service
        self.flow_repo = flow_repository
        self.post_service = post_base_service

    async def generate_auto_posts(self, flow_id: int) -> list[PostDTO]:
        flow = await self.flow_repo.get_flow_by_id(flow_id)
        if not flow:
            return []

        userbot_volume, web_volume = self._calculate_volumes(flow)
        user = await sync_to_async(lambda: flow.channel.user)()

        logging.info(f"Generating posts: userbot={userbot_volume}, web={web_volume}, user: {user}")

        userbot_posts = await self.userbot_service.get_last_posts(flow, userbot_volume)
        web_posts = await self.web_service.get_last_posts(flow, web_volume)
        
        combined_posts = userbot_posts + web_posts
        combined_posts.sort(key=lambda x: x.created_at, reverse=True)
        
        return await self._create_posts_from_dtos(flow, combined_posts)

    def _calculate_volumes(self, flow) -> tuple[int, int]:
        total_volume = flow.flow_volume
        sources = flow.sources

        count_telegram = sum(1 for item in sources if item['type'] == 'telegram')
        count_web = sum(1 for item in sources if item['type'] == 'web')

        total_sources = count_telegram + count_web
        if total_sources == 0:
            return (0, 0)

        base_volume = total_volume // total_sources
        remainder = total_volume % total_sources

        userbot_volume = base_volume * count_telegram
        web_volume = base_volume * count_web

        if remainder:
            web_volume += remainder

        return (userbot_volume, web_volume)

    async def _create_posts_from_dtos(self, flow, post_dtos: list) -> list[PostDTO]:
        generated_posts = []

        for post_dto in post_dtos:
            try:
                if await Post.objects.filter(source_id=post_dto.source_id).aexists():
                    logging.info(f"Skipping duplicate post: {post_dto.source_id}")
                    continue

                media_list = self._prepare_media_list(post_dto)
                post = await self.post_service.post_repo.create_with_media(
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

    def _prepare_media_list(self, post_dto) -> list[dict]:
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
            
        return media_list