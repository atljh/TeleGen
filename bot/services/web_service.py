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
    images: Optional[List[str]] = None

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
            raw_posts = await self._fetch_rss_posts(rss_urls, limit, flow)
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
            
            if not rss_urls and self.rss_app_key and self.rss_app_secret:
                try:
                    api_url = await self._get_rss_via_api(source['link'])
                    if api_url:
                        rss_urls.append(api_url)
                except Exception as e:
                    self.logger.warning(f"RSS.app API failed: {str(e)}")
            
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
                return data.get('rss_feed_url')
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

    async def _fetch_rss_posts(self, rss_urls: List[str], limit: int, flow: FlowDTO) -> List[Dict]:
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
                        'images': self._extract_rss_images(entry) or [],
                        'domain': domain
                    }
                    
                    if entry.link:
                        enriched = await self._parse_with_llm(entry.link, flow)
                        if enriched:
                            post.update({
                                'content': enriched.content,
                                'images': list(set(post['images'] + (enriched.images or [])))
                            })
                    
                    posts.append(post)
            except Exception as e:
                self.logger.error(f"Error parsing RSS feed {rss_url}: {str(e)}")
                
        return posts

    async def _parse_with_llm(self, url: str, flow: FlowDTO) -> Optional[WebPost]:
        try:
            instructions = [
                "1. Извлеки основной текст статьи, удалив рекламу и мусор.",
                "2. Сохрани важные изображения (только URL).",
                "Извлеки только основной текст статьи (без комментариев/рекламы). "
                "Сохрани 1-2 ключевых изображения. Не обрабатывай весь контент."
                f"3. Переведи текст на украинский язык.",
                f"4. Стиль изложения: {flow.theme}.",
            ]

            if flow.use_emojis:
                emoji_type = "премиум" if flow.use_premium_emojis else "обычные"
                instructions.append(f"5. Добавь {emoji_type} эмодзи где уместно.")

            if flow.title_highlight:
                instructions.append("6. Выдели заголовок тегами <b> и добавь пустую строку после него.")

            if flow.cta:
                instructions.append(f"7. Добавь призыв к действию: '{flow.cta}'")

            instructions.append(f"8. Убедись, что текст не превышает {max_chars} символов.")
            instructions.append("9. Верни только обработанный контент без пояснений.")

            prompt = "\n".join(instructions)
            max_chars = {
                "to_100": 100,
                "to_300": 300,
                "to_1000": 1000
            }.get(flow.content_length, 300)

            llm_strat = LLMExtractionStrategy(
                llmConfig=LLMConfig(
                    provider="openai/gpt-4o-mini",
                    api_token=self.openai_key
                ),
                schema=WebPost.model_json_schema(),
                extraction_type="schema",
                instruction=prompt,
                chunk_token_threshold=30000,
                apply_chunking=True,
                input_format="html",
                extra_args={
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "top_p": 0.9,
                    "request_timeout": 45
                }
            )

            crawl_config = CrawlerRunConfig(
                extraction_strategy=llm_strat,
                cache_mode=CacheMode.BYPASS,
            )

            result = await self.crawler.arun(url=url, config=crawl_config)

            if not result.success:
                self.logger.error(f"LLM parsing failed for {url}: {result.error_message}")
                return None

            try:
                parsed_data = json.loads(result.extracted_content)
                
                if isinstance(parsed_data, list) and len(parsed_data) > 0:
                    parsed_data = parsed_data[0]
                
                logging.info(f'===*20{parsed_data}')
                if not all(field in parsed_data for field in ['title', 'content', 'url']):
                    raise ValueError("Missing required fields in LLM response")
                
                domain = urlparse(url).netloc
                if flow.signature:
                    parsed_data['content'] = f"{parsed_data['content']}\n\n{flow.signature}\nИсточник: {domain}"
                else:
                    parsed_data['content'] = f"{parsed_data['content']}\n\nИсточник: {domain}"
                
                return WebPost(**parsed_data)
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Invalid LLM response for {url}: {str(e)}")
                return None
                    
        except Exception as e:
            self.logger.error(f"Error during LLM parsing of {url}: {str(e)}", exc_info=True)
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
        
        images = [PostImageDTO(url=img) for img in raw_post.get('images', [])] 
        
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
            images=images,
            media_type='image' if images else None
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
        return images[:3] if images else []