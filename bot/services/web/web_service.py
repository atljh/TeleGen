import asyncio
import logging
from typing import List, Dict, Optional

from pydantic import BaseModel
from bs4 import BeautifulSoup

from bot.database.dtos.dtos import FlowDTO, PostDTO, PostStatus
from bot.services.web.content_processor_service import ContentProcessorService
from bot.services.web.image_extractor_service import ImageExtractorService
from bot.services.web.post_builder_service import PostBuilderService
from bot.services.web.rss_service import RssService
from bot.services.web.web_scraper_service import WebScraperService
from bot.services.user_service import UserService


class WebService:
    def __init__(
        self,
        rss_service: RssService,
        content_processor: ContentProcessorService,
        web_scraper: WebScraperService,
        image_extractor: ImageExtractorService,
        post_builder: PostBuilderService,
        user_service: UserService,
        logger: Optional[logging.Logger] = None
    ):
        self.rss_service = rss_service
        self.content_processor = content_processor
        self.web_scraper = web_scraper
        self.image_extractor = image_extractor
        self.post_builder = post_builder
        self.user_service = user_service
        self.logger = logger or logging.getLogger(__name__)

    async def get_last_posts(
        self, 
        flow: FlowDTO, 
        limit: int = 10
    ) -> List[PostDTO]:
        try:
            raw_posts = await self._get_raw_posts(flow, limit)
            enriched_posts = await self._enrich_posts(raw_posts)
            return await self._process_and_build_posts(enriched_posts, flow)
        except Exception as e:
            self.logger.error(f"Failed to get posts: {e}", exc_info=True)
            return []

    async def _get_raw_posts(
        self, 
        flow: FlowDTO, 
        limit: int
    ) -> List[Dict]:
        return await self.rss_service.get_posts_for_flow(flow, limit)

    async def _enrich_posts(
        self, 
        posts: List[Dict]
    ) -> List[Dict]:
        return await asyncio.gather(*[
            self._enrich_single_post(post)
            for post in posts
        ])

    async def _enrich_single_post(
        self, 
        post: Dict
    ) -> Dict:
        if not post.get('original_link'):
            return post

        try:
            web_data = await self.web_scraper.scrape_page(post['original_link'])
            if not web_data:
                return post

            if not post.get('images'):
                html = await self.web_scraper.fetch_html(post['original_link'])
                soup = BeautifulSoup(html, 'html.parser') if html else None
                if soup:
                    web_data.images = self.image_extractor.extract_images(
                        soup, 
                        post['original_link']
                    )

            return {**post, **web_data.model_dump()}
        except Exception as e:
            self.logger.warning(f"Failed to enrich post: {e}")
            return post

    async def _process_and_build_posts(
        self, 
        posts: List[Dict], 
        flow: FlowDTO
    ) -> List[PostDTO]:
        user = await self.user_service.get_user_by_flow(flow)
        processed_contents = await self.content_processor.process_batch(
            [p['content'] for p in posts],
            flow,
            user.id
        )

        return [
            self.post_builder.build_post(post, content, flow)
            for post, content in zip(posts, processed_contents)
            if not isinstance(content, Exception)
        ]