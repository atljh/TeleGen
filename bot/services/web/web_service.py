import asyncio
import logging
from typing import Awaitable, Callable, List, Dict, Optional

from pydantic import BaseModel
from bs4 import BeautifulSoup

from bot.database.dtos.dtos import FlowDTO, PostDTO, PostStatus


class WebService:
    def __init__(
        self,
        rss_service_factory: Callable[[], Awaitable['RssService']],
        content_processor: 'ContentProcessorService',
        user_service: 'UserService',
        flow_service: 'FlowService',
        web_scraper: 'WebScraperService',
        aisettings_service: 'AISettingsService',
        image_extractor: 'ImageExtractorService',
        post_builder: 'PostBuilderService',
        logger: logging.Logger | None = None

    ):
        self.rss_service_factory = rss_service_factory
        self.content_processor = content_processor
        self.user_service = user_service
        self.flow_service = flow_service
        self.web_scraper = web_scraper
        self.aisettings_service = aisettings_service
        self.image_extractor = image_extractor
        self.post_builder = post_builder
        self.logger = logger or logging.getLogger(__name__)

    async def get_last_posts(
        self, 
        flow: FlowDTO, 
        limit: int = 10
    ) -> List[PostDTO]:
        async with self.rss_service_factory() as rss_service:
            try:
                raw_posts = [
                    post async for post in 
                    rss_service.get_posts_for_flow(flow, self.flow_service, limit)
                ][:limit]
                
                enriched_posts = await self._enrich_posts(raw_posts)
                return await self._process_and_build_posts(enriched_posts, flow)
                
            except Exception as e:
                self.logger.error(f"Failed to get posts: {e}", exc_info=True)
                return []

    async def _get_raw_posts(
        self, 
        rss_service: 'RssService',
        flow: FlowDTO, 
        limit: int
    ) -> List[Dict]:
        return [
            post async for post in 
            rss_service.get_posts_for_flow(flow, self.flow_service, limit)
        ][:limit]

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