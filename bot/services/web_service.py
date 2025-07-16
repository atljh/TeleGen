import json
import os
import time
import asyncio
import logging
import tempfile
import hashlib
import feedparser
import aiohttp
import random
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional, List, Dict
from pydantic import BaseModel
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

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
        
        # Настройки задержек для избежания блокировки
        self.min_delay = 2.0
        self.max_delay = 7.0
        self.request_timeout = 30
        
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
        
        # Инициализация HTTP-клиента с пользовательскими заголовками
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            },
            timeout=aiohttp.ClientTimeout(total=self.request_timeout)
        )

    async def _random_delay(self):
        """Добавляет случайную задержку между запросами"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            start_time = time.time()
            logging.info("____START WEB GENERATE____")
            rss_urls = await self._discover_rss_urls(flow.sources)
            logging.info(f"====RSS URLS: {rss_urls}")
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
            
            await self._random_delay()
            
            base_url = source['link'].rstrip('/')
            for path in self.common_rss_paths:
                rss_url = f"{base_url}{path}"
                if await self._validate_rss_feed(rss_url):
                    rss_urls.append(rss_url)
                    break
            
            if not rss_urls and self.rss_app_key and self.rss_app_secret:
                try:
                    await self._random_delay()
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
        
        try:
            async with self.session.post(
                "https://api.rss.app/v1/feeds",
                headers=headers,
                json={"url": url},
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logging.info(f'-=-=-=-=-'*20, data)
                    return data.get('rss_feed_url')
                return None
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
            return None

    async def _validate_rss_feed(self, url: str) -> bool:
        try:
            if url in self.rss_cache:
                return self.rss_cache[url]
                
            await self._random_delay()
            async with self.session.get(url) as response:
                if response.status != 200:
                    return False
                
                text = await response.text()
                feed = feedparser.parse(text)
                is_valid = len(feed.entries) > 0
                self.rss_cache[url] = is_valid
                return is_valid
        except Exception:
            return False

    async def _fetch_rss_posts(self, rss_urls: List[str], limit: int, flow: FlowDTO) -> List[Dict]:
        posts = []
        
        for rss_url in rss_urls:
            try:
                await self._random_delay()
                async with self.session.get(rss_url) as response:
                    if response.status != 200:
                        continue
                    
                    text = await response.text()
                    feed = feedparser.parse(text)
                    domain = urlparse(rss_url).netloc
                    
                    for entry in feed.entries[:limit]:
                        await self._random_delay()
                        
                        self.logger.info(f'-------'*10, entry)
                        post = {
                            'title': entry.title,
                            'content': getattr(entry, 'description', None) or getattr(entry, 'summary', None) or entry.title,
                            'original_link': entry.link,
                            'original_date': self._parse_rss_date(entry.get('published')),
                            'source_url': rss_url,
                            'source_id': f"rss_{hashlib.md5(entry.link.encode()).hexdigest()}",
                            'images': self._extract_rss_images(entry) or [],
                            'domain': domain
                        }
                        
                        if entry.link:
                            await self._random_delay()
                            enriched = await self._parse_web_page(entry.link, flow)
                            if enriched:
                                post.update({
                                    'content': enriched.content,
                                    'images': list(set(post['images'] + (enriched.images or [])))
                                })
                        
                        posts.append(post)
            except Exception as e:
                self.logger.error(f"Error parsing RSS feed {rss_url}: {str(e)}")
                
        return posts

    async def _parse_web_page(self, url: str, flow: FlowDTO) -> Optional[WebPost]:
        try:
            await self._random_delay()
            
            # Получаем HTML страницы
            html = await self._fetch_html(url)
            if not html:
                return None
                
            # Извлекаем основной контент
            cleaned_html = self._extract_article_only(html)
            if not cleaned_html:
                return None
                
            # Создаем объект BeautifulSoup для парсинга
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            
            # Извлекаем заголовок
            title = soup.find('title').get_text() if soup.find('title') else "Без заголовка"
            
            # Извлекаем текст статьи
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # Извлекаем изображения (первые 3)
            images = []
            for img in soup.find_all('img', src=True)[:3]:
                img_url = img['src']
                if not img_url.startswith(('http', 'https')):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    img_url = base_url + ('' if img_url.startswith('/') else '/') + img_url
                images.append(img_url)
            
            # Обрабатываем контент согласно настройкам flow
            processed_content = await self._process_web_content(content, flow)
            
            return WebPost(
                title=title,
                content=processed_content,
                date=str(datetime.now()),
                source=urlparse(url).netloc,
                url=url,
                images=images
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing web page {url}: {str(e)}")
            return None

    async def _process_web_content(self, content: str, flow: FlowDTO) -> str:
        """Обрабатывает контент согласно настройкам flow"""
        processed = content
        
        # Базовая обработка
        processed = await DefaultContentProcessor().process(processed)
        
        # Обработка с ChatGPT если доступен ключ
        if self.openai_key:
            async with self._semaphore:
                processed = await self._process_with_chatgpt(processed, flow)
        
        # Добавляем подпись если нужно
        if flow.signature:
            processed = f"{processed}\n\n{flow.signature}"
        
        return processed

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
        
        return post_dto

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

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[datetime]:
        try:
            return date_parser.parse(date_str)
        except Exception:
            return None
        
    def _extract_article_only(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "footer", "header", "nav", "aside"]):
            tag.decompose()

        # Пробуем найти основной контент
        article = soup.find("article") or soup.find("main") or soup.find("div", class_=lambda x: x and 'content' in x.lower())
        return str(article) if article else str(soup)

    async def _fetch_html(self, url: str) -> Optional[str]:
        try:
            await self._random_delay()
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            self.logger.error(f"Failed to fetch HTML from {url}: {str(e)}")
            return None