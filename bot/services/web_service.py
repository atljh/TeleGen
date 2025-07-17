import re
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
        
        self.max_concurrent_requests = 10
        self.request_timeout = 30
        self.min_delay = 1.0
        self.max_delay = 3.0
        
        self.rss_cache = {}
        self.html_cache = {}
        
        self.common_rss_paths = [
            '/feed', '/rss', '/atom.xml', '/feed.xml', '/rss.xml',
            '/blog/feed', '/news/feed', '/feed/rss', '/feed/atom'
        ]
        self.skip_image_classes = {
            'icon', 'logo', 'button', 'badge', 
            'app-store', 'google-play', 'download'
        }
        self.skip_alt_words = {
            'download', 'app store', 'google play', 'get it on',
            'available on', 'button', 'logo', 'badge'
        }

        self.news_block_classes = {
            'post_news_photo', 'news-image', 'article-image',
            'post-image', 'news-photo', 'story-image'
        }
        self.min_news_image_size = (400, 250)

        self.session = aiohttp.ClientSession(
            headers=self._generate_headers(),
            timeout=aiohttp.ClientTimeout(total=self.request_timeout)
        )

    def _generate_headers(self) -> Dict:
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
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        try:
            start_time = time.time()
            self.logger.info("Starting parallel posts processing")
            
            rss_urls = await self._discover_rss_urls_parallel(flow.sources)
            self.logger.info(f"Discovered RSS URLs: {rss_urls}")
            
            if not rss_urls:
                self.logger.warning("No RSS URLs found after all attempts")
                return []
            
            await self._random_delay()
            
            raw_posts = await self._fetch_rss_posts_parallel(rss_urls, limit, flow)
            processed_posts = await self._process_posts_batch(raw_posts, flow)
            
            self.logger.info(
                f"Processed {len(processed_posts)} posts in {time.time() - start_time:.2f}s, "
                f"avg {len(processed_posts)/(time.time()-start_time):.2f} posts/sec"
            )
            return processed_posts[:limit]
        except Exception as e:
            self.logger.error(f"Error in get_last_posts: {str(e)}", exc_info=True)
            return []

    async def _discover_rss_urls_parallel(self, sources: List[Dict], max_retries: int = 3) -> List[str]:
        tasks = []
        discovered_urls = []
        
        for source in sources:
            if source['type'] != 'web':
                continue
                
            tasks.append(self._discover_rss_for_source(source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        discovered_urls = [url for url in results if url and not isinstance(url, Exception)]
        
        retry_count = 0
        while not discovered_urls and retry_count < max_retries:
            retry_count += 1
            self.logger.info(f"No RSS URLs found, retrying ({retry_count}/{max_retries})...")
            
            retry_delay = random.uniform(3.0, 5.0) * retry_count
            await asyncio.sleep(retry_delay)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            discovered_urls = [url for url in results if url and not isinstance(url, Exception)]
        
        return discovered_urls

    async def _discover_rss_for_source(self, source: Dict) -> Optional[str]:
        
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
                
                post_tasks = []
                for entry in feed.entries[:limit]:
                    post_tasks.append(self._process_rss_entry(entry, domain, rss_url, flow))
                
                return await asyncio.gather(*post_tasks)
        except Exception as e:
            self.logger.error(f"Error parsing RSS feed {rss_url}: {str(e)}")
            return []

    async def _process_rss_entry(self, entry, domain: str, rss_url: str, flow: FlowDTO) -> Dict:
        await self._random_delay()
        
        post = {
            'title': entry.title,
            'content': getattr(entry, 'description', None) or getattr(entry, 'summary', None) or entry.title,
            'original_link': entry.link,
            'original_date': self._parse_rss_date(entry.get('published')),
            'source_url': rss_url,
            'source_id': f"rss_{hashlib.md5(entry.link.encode()).hexdigest()}",
            'images': self._extract_rss_images(entry),
            # 'images': [],
            'domain': domain
        }
        
        if entry.link:
            enriched = await self._parse_web_page(entry.link, flow)
            if enriched:
                combined_images = list({img: None for img in post['images'] + (enriched.images or [])}.keys())
                post.update({
                    'content': enriched.content,
                    'images': combined_images[:5]
                })
        
        return post

    async def _process_posts_batch(self, raw_posts: List[Dict], flow: FlowDTO) -> List[PostDTO]:
        if not raw_posts:
            return []
        
        contents = [post['content'] for post in raw_posts]
        
        if self.openai_key:
            try:
                processed_contents = await self._process_with_chatgpt_batch(contents, flow)
            except Exception as e:
                self.logger.error(f"Error in batch ChatGPT processing: {str(e)}")
                processed_contents = contents
        else:
            processed_contents = await asyncio.gather(*[
                DefaultContentProcessor().process(content) 
                for content in contents
            ])
        
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
        try:
            await self._random_delay()
            html = await self._fetch_html(url)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            article = soup.find('article') or soup.find('main') or soup.body
            text = article.get_text(separator='\n', strip=True) if article else ''
            
            self.logger.info(f'Parse images============')
            images = self._extract_quality_images(soup, url)
            self.logger.info(f'====================={images}')

            return WebPost(
                title=soup.title.string if soup.title else url,
                content=text,
                date=str(datetime.now()),
                source=urlparse(url).netloc,
                url=url,
                images=images
            )
        except Exception as e:
            self.logger.error(f"Error parsing web page {url}: {str(e)}")
            return None
        
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
                    return data.get('rss_feed_url')
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)} {e}")
        return None

    async def _validate_rss_feed(self, url: str) -> bool:
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
        try:
            await self._random_delay()
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            self.logger.error(f"Failed to fetch HTML from {url}: {str(e)}")
        return None

    def _extract_rss_images(self, entry) -> List[str]:
        images = []
        
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('type', '').startswith('image/') and not media.get('url', '').endswith('.svg'):
                    images.append(media['url'])
        
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('type', '').startswith('image/') and not link.get('href', '').endswith('.svg'):
                    images.append(link['href'])
        
        return list(dict.fromkeys(images))[:3]

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[datetime]:
        try:
            return date_parser.parse(date_str)
        except Exception:
            return None

    async def close(self):
        await self.session.close()

    def _has_news_caption(self, img_tag) -> bool:
        """Проверяет наличие новостной подписи к изображению"""
        for parent in img_tag.parents:
            # Проверка соседних элементов с подписями
            siblings = parent.find_next_siblings()
            for sibling in siblings:
                sibling_classes = sibling.get('class', [])
                if isinstance(sibling_classes, str):
                    sibling_classes = sibling_classes.split()
                
                if any(cls in ['caption', 'source', 'credit', 'description'] 
                    for cls in sibling_classes):
                    return True
        
        return False

    def _extract_quality_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        images = []
        
        # 1. Сначала проверяем все теги picture (часто содержат новостные фото)
        for picture in soup.find_all('picture'):
            img = picture.find('img', src=True)
            if img:
                img_url = self._get_image_url(img, base_url)
                if img_url:
                    if not self._should_skip_image(img, img_url):
                        self.logger.debug(f"Adding news image: {img_url}")
                        images.append(img_url)
                    else:
                        self.logger.debug(f"Skipping image (news check failed): {img_url}")
        
        # 2. Затем обычные img (кроме уже обработанных в picture)
        for img in soup.find_all('img'):
            if img.parent and img.parent.name == 'picture':
                continue
                
            img_url = self._get_image_url(img, base_url)
            if img_url and not self._should_skip_image(img, img_url):
                images.append(img_url)
        
        # Удаляем дубликаты и ограничиваем количество
        unique_images = list(dict.fromkeys(images))
        return unique_images[:5]

    def _is_news_image(self, img_url: str) -> bool:
        """Проверяет, похоже ли изображение на новостное"""
        news_paths = {'/images/', '/photos/', '/media/', '/documents/', '/news/'}
        img_url_lower = img_url.lower()
        return any(path in img_url_lower for path in news_paths)

    def _should_skip_by_parent(self, img_tag) -> bool:
        for parent in img_tag.parents:
            parent_classes = parent.get('class', [])
            if isinstance(parent_classes, str):
                parent_classes = parent_classes.split()
            
            skip_parent_classes = {
                'footer', 'header', 'sidebar', 'ad', 'banner',
                'app-links', 'download-section', 'badges'
            }
            if any(cls in parent_classes for cls in skip_parent_classes):
                return True
            
            if parent.name == 'a' and 'download' in parent.get('href', '').lower():
                return True
        
        return False

    def _get_image_url(self, img_tag, base_url: str) -> Optional[str]:
        for attr in ['data-src', 'src', 'data-original', 'data-srcset']:
            img_url = img_tag.get(attr)
            if img_url:
                if attr == 'data-srcset':
                    img_url = img_url.split(',')[0].split()[0]
                return self._normalize_image_url(img_url, base_url)
        return None

    def _should_skip_image(self, img_tag, img_url: str) -> bool:
        """Определяет, нужно ли пропустить изображение с точной проверкой контекста"""
        # 1. Абсолютные исключения (SVG, data-URL, GIF)
        if (img_url.lower().endswith('.svg') or 
            img_url.startswith('data:') or
            img_url.lower().endswith('.gif')):
            return True
        
        # 2. Проверка новостного контекста (если в новостном блоке - НЕ пропускаем)
        if self._is_in_news_block(img_tag):
            return False
        
        # 3. Проверка размеров (только для НЕ новостных изображений)
        if self._is_tiny_or_decorative(img_tag):
            return True
        
        # 4. Проверка по классам (только строго декоративные)
        decorative_classes = {
            'icon', 'logo', 'button', 'badge', 
            'app-store', 'google-play', 'download',
            'spinner', 'loader', 'ad', 'banner'
        }
        img_classes = img_tag.get('class', [])
        if isinstance(img_classes, str):
            img_classes = img_classes.split()
        
        if any(cls in decorative_classes for cls in img_classes):
            return True
        
        # 5. Проверка по alt-тексту
        alt_text = img_tag.get('alt', '').lower()
        skip_alt_words = {
            'download', 'app store', 'google play', 
            'button', 'logo', 'badge', 'реклама', 'ad'
        }
        if any(word in alt_text for word in skip_alt_words):
            return True
        
        # 6. Проверка URL (исключаем только явно декоративные)
        decorative_url_parts = {
            '/buttons/', '/badges/', '/logos/', 
            '/ads/', '/banners/', '/downloads/',
            '/userpics/', '/avatars/'
        }
        img_url_lower = img_url.lower()
        if any(part in img_url_lower for part in decorative_url_parts):
            return True
        
        return False

    def _is_tiny_or_decorative(self, img_tag) -> bool:
        """Проверяет, является ли изображение слишком маленьким или декоративным"""
        if self._is_in_news_block(img_tag):
            return False
        
        width = self._get_image_dimension(img_tag, 'width')
        height = self._get_image_dimension(img_tag, 'height')
        
        # Минимальные размеры для новостных изображений
        min_news_width = 400
        min_news_height = 250
        
        # Если размеры не указаны, считаем что подходит
        if not width or not height:
            return False
        
        # Проверяем размеры
        if width < min_news_width or height < min_news_height:
            return True
        
        # Проверяем инлайновые стили
        style = img_tag.get('style', '')
        if ('width:' in style or 'height:' in style):
            try:
                width_match = re.search(r'width:\s*(\d+)px', style)
                height_match = re.search(r'height:\s*(\d+)px', style)
                
                if width_match and height_match:
                    style_width = int(width_match.group(1))
                    style_height = int(height_match.group(1))
                    if style_width < min_news_width or style_height < min_news_height:
                        return True
            except (AttributeError, ValueError):
                pass
        
        return False

    def _is_in_news_block(self, img_tag) -> bool:
        """Проверяет, находится ли изображение в новостном блоке"""
        news_block_classes = {
            'post_news_photo', 'news-image', 'article-image',
            'post-image', 'news-photo', 'story-image',
            'article-photo', 'news-media', 'media-image'
        }
        
        for parent in img_tag.parents:
            # Проверка классов родителя
            parent_classes = parent.get('class', [])
            if isinstance(parent_classes, str):
                parent_classes = parent_classes.split()
            
            if any(cls in news_block_classes for cls in parent_classes):
                return True
            
            # Дополнительные признаки новостного блока
            if parent.name == 'div' and any(
                sibling.name in ['div', 'figcaption'] and 
                any(cls in ['caption', 'source', 'credit'] 
                    for cls in sibling.get('class', []))
                for sibling in parent.find_next_siblings()
            ):
                return True
        
        return False

    def _is_tiny_image(self, img_tag) -> bool:
        """Проверяет, является ли изображение слишком маленьким"""
        width = self._get_image_dimension(img_tag, 'width')
        height = self._get_image_dimension(img_tag, 'height')
        
        # Минимальные размеры для новостных изображений
        min_width = 300
        min_height = 200
        
        # Если размеры не указаны, считаем что подходит
        if not width or not height:
            return False
        
        # Проверяем явно указанные размеры
        if width < min_width or height < min_height:
            return True
        
        # Проверяем инлайновые стили
        style = img_tag.get('style', '')
        if ('width:' in style or 'height:' in style):
            try:
                # Ищем ширину в стилях
                width_match = re.search(r'width:\s*(\d+)px', style)
                height_match = re.search(r'height:\s*(\d+)px', style)
                
                if width_match and height_match:
                    style_width = int(width_match.group(1))
                    style_height = int(height_match.group(1))
                    if style_width < min_width or style_height < min_height:
                        return True
            except (AttributeError, ValueError):
                pass
        
        return False

    def _normalize_image_url(self, img_url: str, base_url: str) -> str:
        """Нормализует URL изображения"""
        if img_url.startswith(('http://', 'https://')):
            return img_url
            
        parsed_base = urlparse(base_url)
        if img_url.startswith('//'):
            return f"{parsed_base.scheme}:{img_url}"
        elif img_url.startswith('/'):
            return f"{parsed_base.scheme}://{parsed_base.netloc}{img_url}"
        else:
            return f"{parsed_base.scheme}://{parsed_base.netloc}/{img_url}"

    def _get_image_dimension(self, img_tag, dimension: str) -> Optional[int]:
        """Получает размер изображения из атрибутов"""
        value = img_tag.get(dimension)
        if not value:
            return None
            
        try:
            # Удаляем 'px' если есть
            if isinstance(value, str):
                value = value.replace('px', '')
            return int(float(value))
        except (ValueError, TypeError):
            return None