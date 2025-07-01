import json
import os
import time
import asyncio
import logging
import tempfile
import hashlib
import feedparser
import aiohttp
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional, List, Dict
from pydantic import BaseModel

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LLMConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from bot.database.dtos.dtos import FlowDTO, PostDTO, PostImageDTO, PostStatus
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
        rss_app_key: str = None,
        rss_app_secret: str = None
    ):
        self.logger = logging.getLogger(__name__)
        self.openai_key = openai_key
        self.rss_app_key = rss_app_key
        self.rss_app_secret = rss_app_secret
        self._semaphore = asyncio.Semaphore(10)
        self.user_service = user_service
        self.aisettings_service = aisettings_service
        self.download_semaphore = asyncio.Semaphore(5)
        
        self.rss_cache = {}
        self.common_rss_paths = [
            '/feed',
            '/rss',
            '/atom.xml',
            '/feed.xml',
            '/rss.xml',
            '/blog/feed',
            '/news/feed',
            '/feed/rss',
            '/feed/atom'
        ]
        
        self.crawler = AsyncWebCrawler(config=BrowserConfig(headless=True))
        self.session = aiohttp.ClientSession()

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            start_time = time.time()
            logging.info("____START WEB GENERATE____")
            rss_urls = await self._discover_rss_urls(flow.sources)
            raw_posts = await self._fetch_rss_posts(rss_urls, limit)
            processed_posts = await self._process_posts_parallel(raw_posts, flow)

            self.logger.info(f"[WEB] Processed {len(processed_posts)} posts in {time.time() - start_time:.2f}s")
            return processed_posts[:limit]
        except Exception as e:
            self.logger.error(f"Error getting posts: {str(e)}")
            return []

    async def _discover_rss_urls(self, sources: List[Dict]) -> List[str]:
        rss_urls = []
        
        for source in sources:
            if source['type'] != 'web':
                continue
            
            base_url = source['link'].rstrip('/')
            for path in self.common_rss_paths:
                rss_url = f"{base_url}{path}"
                if await self._validate_rss_feed(rss_url):
                    rss_urls.append(rss_url)
                    break
            self.logger.info("======RSS NOT FOUND======")
            
            if self.rss_app_key and self.rss_app_secret:
                try:
                    api_url = await self._get_rss_via_api(source['link'])
                    if api_url:
                        rss_urls.append(api_url)
                        continue
                except Exception as e:
                    self.logger.warning(f"RSS.app API failed: {str(e)}")
            
            else:
                self.logger.warning(f"RSS feed not found for {source['link']}")
                
        return rss_urls

    async def _get_rss_via_api(self, url: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.rss_app_key}:{self.rss_app_secret}",
            "Content-Type": "application/json"
        }
        
        async with self.session.post(
            "https://api.rss.app/v1/feeds",
            headers=headers,
            json={"url": url},
            timeout=10
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.debug(f"RSS.app API response: {data.get('rss_feed_url')}")
                
                return data.get('rss_feed_url')
            else:
                self.logger.error(f"RSS.app API failed: {response.status} - {await response.text()}")
                return None

    async def _validate_rss_feed(self, url: str) -> bool:
        try:
            if url in self.rss_cache:
                return self.rss_cache[url]
                
            feed = feedparser.parse(url)
            is_valid = len(feed.entries) > 0
            self.rss_cache[url] = is_valid
            return is_valid
        except Exception:
            return False

    async def _fetch_rss_posts(self, rss_urls: List[str], limit: int) -> List[Dict]:
        posts = []
        
        for rss_url in rss_urls:
            try:
                feed = feedparser.parse(rss_url)
                domain = urlparse(rss_url).netloc
                
                for entry in feed.entries[:limit]:
                    post = {
                        'title': entry.title,
                        'content': entry.description or entry.title,
                        'original_link': entry.link,
                        'original_date': self._parse_rss_date(entry.get('published')),
                        'source_url': rss_url,
                        'source_id': f"rss_{hashlib.md5(entry.link.encode()).hexdigest()}",
                        'images': self._extract_rss_images(entry),
                        'domain': domain
                    }
                    self.logger.info(post)
                    if entry.link:
                        enriched = await self._parse_with_llm(entry.link)
                        if enriched:
                            post.update({
                                'content': enriched.content,
                                'images': list(set(post['images'] + (enriched.images or [])))
                            })
                    
                    posts.append(post)
            except Exception as e:
                self.logger.error(f"Error parsing RSS feed {rss_url}: {str(e)}")
                
        return posts

    async def _parse_with_llm(self, url: str) -> Optional[WebPost]:
        logging.info(f"========123213=================={self.openai_key}")
        llm_strat = LLMExtractionStrategy(
            llmConfig=LLMConfig(
                provider="ollama/llama3",
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
            apply_chunking=False,
            input_format="html",
            extra_args={
                "temperature": 0.2,
                "max_tokens": 2000,
                "top_p": 0.9
            }
        )

        crawl_config = CrawlerRunConfig(
            extraction_strategy=llm_strat,
            cache_mode=CacheMode.BYPASS
        )

        try:
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                result = await crawler.arun(url=url, config=crawl_config)

                if not result.success:
                    self.logger.error(f"LLM parsing failed for {url}: {result.error_message}")
                    return None

                try:
                    parsed_data = json.loads(result.extracted_content)
                    
                    if isinstance(parsed_data, list):
                        if len(parsed_data) > 0:
                            parsed_data = parsed_data[0]
                        else:
                            self.logger.error(f"Empty list returned for {url}")
                            return None
                    
                    if 'url' not in parsed_data:
                        parsed_data['url'] = url
                    
                    if 'images' not in parsed_data:
                        parsed_data['images'] = []
                    elif not isinstance(parsed_data['images'], list):
                        parsed_data['images'] = [parsed_data['images']]
                    
                    return WebPost(**parsed_data)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON response for {url}: {str(e)}")
                    return None
                except Exception as e:
                    self.logger.error(f"Error parsing LLM response for {url}: {str(e)}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error during LLM parsing of {url}: {str(e)}")
            return None

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
            self.logger.warning(f"Web Post processing failed: {str(e)}")
            return None

    async def _process_single_post(self, raw_post: Dict, flow: FlowDTO) -> PostDTO:
        domain = raw_post.get('domain', '')
        signature = f"{flow.signature}\n\nИсточник: {domain}" if flow.signature else f"Источник: {domain}"
        
        post_dto = PostDTO(
            id=None,
            flow_id=flow.id,
            content=raw_post['content'],
            source_id=raw_post['source_id'],
            source_url=raw_post['source_url'],
            original_link=raw_post['original_link'],
            original_date=raw_post['original_date'],
            created_at=datetime.now(),
            status=PostStatus.DRAFT,
            images=[PostImageDTO(url=img) for img in raw_post.get('images', [])],
            media_type='image' if raw_post.get('images') else None
        )
        
        processed_text = await self._process_content(post_dto.content, flow)
        return post_dto.copy(update={'content': processed_text})

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

    async def close(self):
        await self.session.close()
        await self.crawler.close()

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