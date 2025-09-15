from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from bs4 import BeautifulSoup

from bot.database.models import FlowDTO, PostDTO
from bot.database.repositories.post_repository import PostRepository
from bot.services.aisettings_service import AISettingsService
from bot.services.flow_service import FlowService
from bot.services.user_service import UserService
from bot.services.web.content_processor_service import ContentProcessorService
from bot.services.web.image_extractor_service import ImageExtractorService
from bot.services.web.post_builder_service import PostBuilderService
from bot.services.web.rss_service import RssService
from bot.services.web.web_scraper_service import WebScraperService


class WebService:
    def __init__(
        self,
        post_repository: PostRepository,
        rss_service_factory: Callable[[], Awaitable[RssService]],
        content_processor: ContentProcessorService,
        user_service: UserService,
        flow_service: FlowService,
        web_scraper: WebScraperService,
        aisettings_service: AISettingsService,
        image_extractor: ImageExtractorService,
        post_builder: PostBuilderService,
        logger: logging.Logger | None = None,
    ):
        self.post_repository = post_repository
        self.rss_service_factory = rss_service_factory
        self.content_processor = content_processor
        self.user_service = user_service
        self.flow_service = flow_service
        self.web_scraper = web_scraper
        self.aisettings_service = aisettings_service
        self.image_extractor = image_extractor
        self.post_builder = post_builder
        self.logger = logger or logging.getLogger(__name__)

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> list[PostDTO]:
        async with self.rss_service_factory() as rss_service:
            try:
                raw_posts = [
                    post
                    async for post in rss_service.get_posts_for_flow(
                        flow,
                        self.flow_service,
                        limit,
                    )
                ][:limit]
                enriched_posts = await self._enrich_posts(raw_posts)
                return await self._process_and_build_posts(enriched_posts, flow)

            except Exception as e:
                self.logger.error(f"Failed to get posts: {e}", exc_info=True)
                return []

    async def _enrich_posts(self, posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await asyncio.gather(*[self._enrich_single_post(post) for post in posts])

    async def _enrich_single_post(self, post: dict) -> dict | None:
        if not post:
            return None
        if not post.get("original_link"):
            return post
        try:
            web_data = await self.web_scraper.scrape_page(post["original_link"])
            if not web_data:
                return post

            if not post.get("images"):
                html = await self.web_scraper._fetch_html(post["original_link"])
                soup = BeautifulSoup(html, "html.parser") if html else None
                if soup:
                    web_data.images = self.image_extractor.extract_images(
                        soup, post["original_link"]
                    )
            else:
                web_data.images = post.get("images")
            return {**post, **web_data.to_dict()}
        except Exception as e:
            self.logger.warning(f"Failed to enrich post: {e}")
            return post

    async def _process_and_build_posts(
        self, posts: list[dict | None], flow: FlowDTO
    ) -> list[PostDTO]:
        if not posts:
            return []

        try:
            await self.user_service.get_user_by_flow(flow)

            valid_posts = [
                p
                for p in posts
                if p is not None and isinstance(p, dict) and "content" in p
            ]

            if not valid_posts:
                self.logger.warning(f"No valid posts found for flow {flow.id}")
                return []

            processed_contents = await self.content_processor.process_batch(
                [p["content"] for p in valid_posts], flow
            )

            result = []
            for post, content in zip(valid_posts, processed_contents, strict=False):
                if isinstance(content, Exception):
                    self.logger.warning(
                        f"Content processing failed for post {post.get('source_id')}: {content}"
                    )
                    continue

                try:
                    built_post = self.post_builder.build_post(post, content, flow)
                    result.append(built_post)
                except Exception as e:
                    self.logger.error(
                        f"Failed to build post {post.get('source_id')}: {e}",
                        exc_info=True,
                    )

            return result

        except Exception as e:
            self.logger.error(
                f"Error in _process_and_build_posts for flow {flow.id}: {e}",
                exc_info=True,
            )
            return []
