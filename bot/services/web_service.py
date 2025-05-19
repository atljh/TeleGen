import json
import os
import time
import asyncio
import logging
import tempfile
import hashlib
import feedparser
from datetime import datetime
from typing import Optional, List, Dict, AsyncGenerator
from contextlib import asynccontextmanager
from pydantic import BaseModel

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from bot.database.dtos.dtos import FlowDTO, PostDTO
from admin_panel.admin_panel.models import PostImage, Post
from bot.services.content_processing.processors import ChatGPTContentProcessor, DefaultContentProcessor
from bot.services.aisettings_service import AISettingsService
from bot.services.user_service import UserService
from bot.utils.notifications import notify_admins

class WebPost(BaseModel):
    title: str
    content: str
    date: Optional[str]
    source: Optional[str]
    url: str
    images: Optional[List[str]]

class WebService:
    def __init__(
        self,
        aisettings_service: AISettingsService,
        user_service: UserService,
        openai_key: str = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.openai_key = openai_key
        self._semaphore = asyncio.Semaphore(10)
        self.user_service = user_service
        self.aisettings_service = aisettings_service
        self.download_semaphore = asyncio.Semaphore(5)

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            start_time = time.time()
            raw_posts = await self._fetch_posts(flow.sources, limit)
            processed_posts = await self._process_posts_parallel(raw_posts, flow)
            unique_posts = await self._filter_existing_posts(processed_posts)
            
            self.logger.info(f"Processed {len(unique_posts)} posts in {time.time() - start_time:.2f}s")
            return unique_posts[:limit]
        except Exception as e:
            self.logger.error(f"Error getting posts: {str(e)}", exc_info=True)
            return []

    async def _fetch_posts(self, sources: List[Dict], limit: int) -> List[Dict]:
        result = []
        source_limits = {}
        
        base_limit = max(1, limit // len(sources))
        for source in sources:
            source_limits[source['link']] = base_limit
        
        remaining = limit - base_limit * len(sources)
        for source in sources[:remaining]:
            source_limits[source['link']] += 1

        for source in sources:
            if len(result) >= limit:
                break

            try:
                remaining_for_source = source_limits[source['link']]
                if remaining_for_source <= 0:
                    continue

                if source['type'] == 'web':
                    post_data = await self._process_web_source(source)
                elif source['type'] == 'rss':
                    post_data = await self._process_rss_source(source, remaining_for_source)
                else:
                    continue

                if post_data:
                    if isinstance(post_data, list):
                        result.extend(post_data[:remaining_for_source])
                    else:
                        result.append(post_data)

            except Exception as e:
                self.logger.error(f"Error processing source {source['link']}: {str(e)}")
                continue

        return result

    async def _process_rss_source(self, source: Dict, limit: int) -> List[Dict]:
        try:
            feed = feedparser.parse(source['url'])
            posts = []
            
            for entry in feed.entries[:limit]:
                source_id = self._generate_source_id(
                    source_type='rss',
                    source_url=source['url'],
                    entry_id=entry.get('id', entry.link),
                    date_str=entry.get('published', '')
                )
                
                post_data = {
                    'title': entry.title,
                    'content': entry.description or entry.title,
                    'original_link': entry.link,
                    'original_date': self._parse_rss_date(entry.get('published')),
                    'source_url': source['url'],
                    'source_id': source_id,
                    'images': self._extract_rss_images(entry)
                }
                posts.append(post_data)
            
            return posts
        except Exception as e:
            self.logger.error(f"Error processing RSS source {source['url']}: {str(e)}")
            return []

    def _generate_source_id(self, source_type: str, source_url: str, entry_id: str, date_str: str) -> str:
        unique_str = f"{source_type}_{source_url}_{entry_id}_{date_str}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        except ValueError:
            return None

    def _extract_rss_images(self, entry) -> List[str]:
        images = []
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    images.append(media['url'])
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('type', '').startswith('image/'):
                    images.append(link['href'])
        return images[:3]

    async def _process_web_source(self, source: Dict) -> Optional[Dict]:
        try:
            web_post = await self._parse_with_llm(source['link'])
            if not web_post:
                return None

            source_id = self._generate_source_id(
                source_type='web',
                source_url=source['link'],
                entry_id=web_post.url,
                date_str=web_post.date or ""
            )

            media_items = []
            if web_post.images:
                media_items = [
                    {'type': 'image', 'url': img, 'file_id': hash(img)}
                    for img in web_post.images[:5]
                ]

            downloaded_media = await self._download_media_batch(media_items)

            return {
                'title': web_post.title,
                'content': web_post.content[:10000],
                'media': downloaded_media,
                'is_album': False,
                'album_size': 0,
                'original_link': web_post.url,
                'original_date': web_post.date or datetime.now(),
                'source_url': source['link'],
                'source_id': source_id
            }
        except Exception as e:
            self.logger.error(f"Error processing web source {source['link']}: {str(e)}")
            return None

    async def _parse_with_llm(self, url: str) -> Optional[WebPost]:
        llm_strat = LLMExtractionStrategy(
            llmConfig=LLMConfig(
                provider="openai/gpt-4o",
                api_token=self.openai_key
            ),
            schema=WebPost.model_json_schema(),
            extraction_type="schema",
            instruction=(
                "From this HTML page, extract structured content with fields:\n"
                "- title (main headline)\n"
                "- content (full article text, 5-10 paragraphs)\n"
                "- date (publication date if available)\n"
                "- source (website or publisher name)\n"
                "- url (original page URL)\n"
                "- images (list of relevant image URLs)\n"
                "Keep the content detailed and well-structured. "
                "Respond only with valid JSON matching the schema."
            ),
            chunk_token_threshold=2000,
            apply_chunking=True,
            input_format="html",
            extra_args={
                "temperature": 0.2,
                "max_tokens": 2000,
                "top_p": 0.9
            }
        )

        crawl_config = CrawlerRunConfig(
            extraction_strategy=llm_strat,
            cache_mode=CacheMode.BYPASS,
            browser_config=BrowserConfig(
                headless=True,
                enable_js=True,
                wait_for_page_load=3,
                scroll_to_bottom=True
            )
        )

        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=crawl_config)
                if result.success:
                    parsed_data = json.loads(result.extracted_content)
                    return WebPost(**parsed_data)
                else:
                    self.logger.error(f"LLM parsing failed for {url}: {result.error_message}")
                    return None
        except Exception as e:
            self.logger.error(f"Error during LLM parsing of {url}: {str(e)}")
            return None

    async def _download_media_batch(self, media_items: List[Dict]) -> List[Dict]:
        if not media_items:
            return []

        self.logger.info(f"Starting download of {len(media_items)} media files...")
        start_time = time.time()
        downloaded = 0
        
        async def _download_with_progress(item):
            nonlocal downloaded
            try:
                path = await self._download_media_file(item['url'], item['type'])
                downloaded += 1
                progress = downloaded / len(media_items) * 100
                elapsed = time.time() - start_time
                self.logger.info(
                    f"Download progress: {downloaded}/{len(media_items)} "
                    f"({progress:.1f}%) | Elapsed: {elapsed:.1f}s"
                )
                return path
            except Exception as e:
                self.logger.error(f"Error downloading {item['type']}: {str(e)}")
                return e
        
        tasks = [_download_with_progress(item) for item in media_items]
        downloaded_paths = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            {**item, 'path': path} 
            for item, path in zip(media_items, downloaded_paths)
            if not isinstance(path, Exception) and path
        ]

    async def _download_media_file(self, url: str, media_type: str) -> Optional[str]:
        async with self.download_semaphore:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{media_type}') as tmp_file:
                    tmp_path = tmp_file.name
                
                # TODO: Реализовать реальную загрузку файла
                # async with aiohttp.ClientSession() as session:
                #     async with session.get(url) as response:
                #         with open(tmp_path, 'wb') as f:
                #             f.write(await response.read())
                
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    return tmp_path
                
                os.unlink(tmp_path)
                return None
                
            except Exception as e:
                self.logger.error(f"Media download failed: {str(e)}")
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None

    async def _filter_existing_posts(self, posts: List[PostDTO]) -> List[PostDTO]:
        if not posts:
            return []
        
        source_ids = [post.source_id for post in posts if post.source_id]
        if not source_ids:
            return posts
        
        existing_ids = set(await Post.objects.filter(source_id__in=source_ids)
                         .values_list('source_id', flat=True)
                         .alist())
        
        return [post for post in posts if post.source_id not in existing_ids]

    async def _process_posts_parallel(self, raw_posts: List[Dict], flow: FlowDTO) -> List[PostDTO]:
        tasks = []
        for raw_post in raw_posts:
            task = self._safe_process_post(raw_post, flow)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, PostDTO)]

    async def _safe_process_post(self, raw_post: Dict, flow: FlowDTO) -> Optional[PostDTO]:
        try:
            return await self._process_single_post(raw_post, flow)
        except Exception as e:
            self.logger.warning(f"Post processing failed: {str(e)}")
            return None

    async def _process_single_post(self, raw_post: Dict, flow: FlowDTO) -> Optional[PostDTO]:
        post_dto = PostDTO.from_raw_post(raw_post)
        
        if not post_dto.content:
            return None

        if isinstance(post_dto.content, list):
            post_dto.content = " ".join(filter(None, post_dto.content))
        
        post_dto.original_link = raw_post.get('original_link')
        post_dto.original_date = raw_post.get('original_date')
        post_dto.source_url = raw_post.get('source_url')
        post_dto.source_id = raw_post.get('source_id')

        try:
            processed_text = await self._process_content(post_dto.content, flow)
            if isinstance(processed_text, list):
                processed_text = " ".join(filter(None, processed_text))
                
            return post_dto.copy(update={
                'content': processed_text,
                'flow_id': flow.id,
                'media_type': self._determine_media_type(raw_post.get('media')),
                'images': self._prepare_images(raw_post.get('media'))
            })
        except Exception as e:
            self.logger.error(f"Error processing post: {str(e)}")
            return None

    def _determine_media_type(self, media_items: List[Dict]) -> Optional[str]:
        if not media_items:
            return None
        return 'image' if media_items[0]['type'] == 'image' else 'video'

    def _prepare_images(self, media_items: List[Dict]) -> List[Dict]:
        if not media_items:
            return []
        return [
            {'url': item['url'], 'path': item.get('path')}
            for item in media_items if item['type'] == 'image'
        ]

    async def _process_content(self, text: str, flow: FlowDTO) -> str:
        text = await DefaultContentProcessor().process(text)
        
        if self.openai_key:
            async with self._semaphore:
                text = await self._process_with_chatgpt(text, flow)
        
        if flow.signature:
            text = f"{text}\n\n{flow.signature}"
        
        return text

    async def _process_with_chatgpt(self, text: str, flow: FlowDTO) -> str:
        user = await self.user_service.get_user_by_flow(flow)
        processor = ChatGPTContentProcessor(
            api_key=self.openai_key,
            flow=flow,
            max_retries=2,
            timeout=15.0,
            aisettings_service=self.aisettings_service
        )
        return await processor.process(text, user.id)