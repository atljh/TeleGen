import json
import os
import time
import asyncio
import logging
import hashlib
import feedparser
import aiohttp
import random
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional, List, Dict, Tuple
from pydantic import BaseModel
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from bot.database.dtos.dtos import FlowDTO, PostDTO, PostImageDTO, PostStatus
from bot.services.content_processing.processors import ChatGPTContentProcessor, DefaultContentProcessor
from bot.services.aisettings_service import AISettingsService
from bot.services.user_service import UserService

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
        self.user_service = user_service
        self.aisettings_service = aisettings_service
        
        # Настройки параллелизма
        self.max_concurrent_requests = 10
        self.request_timeout = 30
        self.min_delay = 1.0
        self.max_delay = 3.0
        
        # Кэширование
        self.rss_cache = {}
        self.html_cache = {}
        
        # Общие пути RSS
        self.common_rss_paths = [
            '/feed', '/rss', '/atom.xml', '/feed.xml', '/rss.xml',
            '/blog/feed', '/news/feed', '/feed/rss', '/feed/atom'
        ]
        
        # HTTP клиент с рандомизированными заголовками
        self.session = aiohttp.ClientSession(
            headers=self._generate_headers(),
            timeout=aiohttp.ClientTimeout(total=self.request_timeout)
        )

    def _generate_headers(self) -> Dict:
        """Генерирует случайные заголовки для запросов"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
        }

    async def _random_delay(self):
        """Добавляет случайную задержку между запросами"""
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        """Основной метод получения постов с параллельной обработкой"""
        try:
            start_time = time.time()
            self.logger.info("Starting parallel posts processing")
            
            # 1. Параллельное обнаружение RSS-лент
            rss_urls = await self._discover_rss_urls_parallel(flow.sources)
            self.logger.info(f"Discovered RSS URLs: {rss_urls}")
            
            if not rss_urls:
                return []
            
            # 2. Параллельная загрузка и обработка постов
            raw_posts = await self._fetch_rss_posts_parallel(rss_urls, limit, flow)
            
            # 3. Пакетная обработка контента
            processed_posts = await self._process_posts_batch(raw_posts, flow)
            
            self.logger.info(
                f"Processed {len(processed_posts)} posts in {time.time() - start_time:.2f}s, "
                f"avg {len(processed_posts)/(time.time()-start_time):.2f} posts/sec"
            )
            return processed_posts[:limit]
        except Exception as e:
            self.logger.error(f"Error in get_last_posts: {str(e)}", exc_info=True)
            return []

    async def _discover_rss_urls_parallel(self, sources: List[Dict]) -> List[str]:
        tasks = []
        
        for source in sources:
            if source['type'] != 'web':
                continue
                
            tasks.append(self._discover_rss_for_source(source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [url for url in results if url and not isinstance(url, Exception)]

    async def _discover_rss_for_source(self, source: Dict) -> Optional[str]:
        await self._random_delay()
        
        base_url = source['link'].rstrip('/')
        
        for path in self.common_rss_paths:
            rss_url = f"{base_url}{path}"
            if await self._validate_rss_feed(rss_url):
                return rss_url
        
        if self.rss_app_key and self.rss_app_secret:
            try:
                await self._random_delay()
                return await self._get_rss_via_api(base_url)
            except Exception as e:
                self.logger.warning(f"RSS.app API failed for {base_url}: {str(e)}")
        
        return None

    async def _fetch_rss_posts_parallel(self, rss_urls: List[str], limit: int, flow: FlowDTO) -> List[Dict]:
        """Параллельная загрузка постов из RSS-лент"""
        tasks = []
        
        for rss_url in rss_urls:
            tasks.append(self._fetch_posts_from_rss(rss_url, limit, flow))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [post for sublist in results if not isinstance(sublist, Exception) 
                for post in sublist]

    async def _fetch_posts_from_rss(self, rss_url: str, limit: int, flow: FlowDTO) -> List[Dict]:
        """Загрузка постов из одной RSS-ленты"""
        try:
            await self._random_delay()
            
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    return []
                
                text = await response.text()
                feed = feedparser.parse(text)
                domain = urlparse(rss_url).netloc
                
                # Создаем задачи для обработки каждого поста
                post_tasks = []
                for entry in feed.entries[:limit]:
                    post_tasks.append(self._process_rss_entry(entry, domain, rss_url, flow))
                
                return await asyncio.gather(*post_tasks)
        except Exception as e:
            self.logger.error(f"Error parsing RSS feed {rss_url}: {str(e)}")
            return []

    async def _process_rss_entry(self, entry, domain: str, rss_url: str, flow: FlowDTO) -> Dict:
        """Обработка одной записи из RSS"""
        await self._random_delay()
        
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
            enriched = await self._parse_web_page(entry.link, flow)
            if enriched:
                post.update({
                    'content': enriched.content,
                    'images': list(set(post['images'] + (enriched.images or [])))
                })
        
        return post

    async def _process_posts_batch(self, raw_posts: List[Dict], flow: FlowDTO) -> List[PostDTO]:
        """Пакетная обработка всех постов"""
        if not raw_posts:
            return []
        
        # 1. Подготовка контента для обработки
        contents = [post['content'] for post in raw_posts]
        
        # 2. Параллельная обработка контента
        if self.openai_key:
            try:
                processed_contents = await self._process_with_chatgpt_batch(contents, flow)
            except Exception as e:
                self.logger.error(f"Error in batch ChatGPT processing: {str(e)}")
                processed_contents = contents  # Возвращаем оригиналы в случае ошибки
        else:
            processed_contents = await asyncio.gather(*[
                DefaultContentProcessor().process(content) 
                for content in contents
            ])
        
        # 3. Сборка результатов
        results = []
        for raw_post, content in zip(raw_posts, processed_contents):
            if isinstance(content, Exception):
                continue
                
            domain = raw_post.get('domain', '')
            signature = f"\n\n{flow.signature}" if flow.signature else ""
            
            images = [PostImageDTO(url=img) for img in raw_post.get('images', [])] 
            
            results.append(PostDTO(
                id=None,
                flow_id=flow.id,
                content=f"{content}{signature}",
                source_id=raw_post['source_id'],
                source_url=raw_post['source_url'],
                original_link=raw_post['original_link'],
                original_date=raw_post['original_date'],
                created_at=datetime.now(),
                status=PostStatus.DRAFT,
                images=images,
                media_type='image' if images else None
            ))
        
        return results

    async def _process_with_chatgpt_batch(self, texts: List[str], flow: FlowDTO) -> List[str]:
        """Пакетная обработка текстов через ChatGPT"""
        user = await self.user_service.get_user_by_flow(flow)
        processor = ChatGPTContentProcessor(
            api_key=self.openai_key,
            flow=flow,
            aisettings_service=self.aisettings_service,
            max_retries=2,
            timeout=30.0
        )
        
        # Обрабатываем весь список текстов сразу (внутри process_batch будет разбивка на батчи)
        return await processor.process_batch(texts, user.id)

    async def _parse_web_page(self, url: str, flow: FlowDTO) -> Optional[WebPost]:
        """Парсинг веб-страницы с кэшированием"""
        if url in self.html_cache:
            return self.html_cache[url]
            
        try:
            await self._random_delay()
            html = await self._fetch_html(url)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлечение основного контента
            article = soup.find('article') or soup.find('main') or soup.body
            text = article.get_text(separator='\n', strip=True) if article else ''
            
            # Извлечение изображений
            images = []
            for img in soup.find_all('img', src=True)[:3]:
                img_url = img['src']
                if not img_url.startswith(('http', 'https')):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    img_url = base_url + ('' if img_url.startswith('/') else '/') + img_url
                images.append(img_url)
            
            result = WebPost(
                title=soup.title.string if soup.title else url,
                content=text,
                date=str(datetime.now()),
                source=urlparse(url).netloc,
                url=url,
                images=images
            )
            
            self.html_cache[url] = result
            return result
        except Exception as e:
            self.logger.error(f"Error parsing web page {url}: {str(e)}")
            return None

    async def _get_rss_via_api(self, url: str) -> Optional[str]:
        """Получение RSS через API"""
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
                    return data.get('rss_feed_url')
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
        return None

    async def _validate_rss_feed(self, url: str) -> bool:
        """Проверка валидности RSS-ленты"""
        if url in self.rss_cache:
            return self.rss_cache[url]
            
        try:
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

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Загрузка HTML страницы"""
        try:
            await self._random_delay()
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            self.logger.error(f"Failed to fetch HTML from {url}: {str(e)}")
        return None

    def _extract_rss_images(self, entry) -> List[str]:
        """Извлечение изображений из RSS записи"""
        images = []
        if hasattr(entry, 'media_content'):
            images.extend(media['url'] for media in entry.media_content 
                         if media.get('type', '').startswith('image/'))
        if hasattr(entry, 'links'):
            images.extend(link['href'] for link in entry.links 
                         if link.get('type', '').startswith('image/'))
        return images[:3]

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Парсинг даты из RSS"""
        try:
            return date_parser.parse(date_str)
        except Exception:
            return None

    async def close(self):
        """Закрытие ресурсов"""
        await self.session.close()