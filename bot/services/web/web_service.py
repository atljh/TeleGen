import asyncio
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel

from bot.database.dtos.dtos import FlowDTO, PostDTO, PostImageDTO, PostStatus
from bot.services.cloudflare_bypass_service import CloudflareBypass
from bot.services.content_processing.processors import ChatGPTContentProcessor, DefaultContentProcessor
from bot.services.aisettings_service import AISettingsService
from bot.services.content_processor_service import ContentProcessorService
from bot.services.image_exctracor_service import ImageExtractorService
from bot.services.post_builder_service import PostBuilderService
from bot.services.user_service import UserService
from bot.services.flow_service import FlowService
from bot.services.web_scraper_service import WebScraperService
from bot.utils.notifications import notify_admins


class WebService:
    def __init__(
        self,
        rss_service,
        content_processor: ContentProcessorService,
        web_scraper: WebScraperService,
        image_extractor: ImageExtractorService,
        post_builder: PostBuilderService,
        user_service: UserService
    ):
        self.rss_service = rss_service
        self.content_processor = content_processor
        self.web_scraper = web_scraper
        self.image_extractor = image_extractor
        self.post_builder = post_builder
        self.user_service = user_service
        self.logger = logging.getLogger(__name__)

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            # 1. Получаем сырые данные из RSS
            raw_posts = await self.rss_service.get_posts_for_flow(flow, limit)
            
            # 2. Обогащаем данными с веб-страниц
            enriched_posts = await self._enrich_posts(raw_posts, flow)
            
            # 3. Обрабатываем контент
            user = await self.user_service.get_user_by_flow(flow)
            processed_contents = await self.content_processor.process_batch(
                [p['content'] for p in enriched_posts],
                flow,
                user.id
            )
            
            # 4. Строим финальные посты
            return [
                self.post_builder.build_post(post, content, flow)
                for post, content in zip(enriched_posts, processed_contents)
                if not isinstance(content, Exception)
            ]
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return []

    async def _enrich_posts(self, posts: List[Dict], flow: FlowDTO) -> List[Dict]:
        async def process_post(post):
            if not post.get('original_link'):
                return post
                
            web_data = await self.web_scraper.scrape_page(post['original_link'])
            if not web_data:
                return post
                
            if not post.get('images'):
                web_data.images = self.image_extractor.extract_images(
                    BeautifulSoup(await self.web_scraper._fetch_html(post['original_link']), 'html.parser'),
                    post['original_link']
                )
                
            return {**post, **web_data.dict()}
            
        return await asyncio.gather(*[process_post(p) for p in posts])