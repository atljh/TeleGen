import os
import re
import json
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
from bot.services.cloudflare_bypass_service import CloudflareBypass
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
        self.cf_bypass = CloudflareBypass(self.logger)
        self.openai_key = openai_key
        self.rss_app_key = rss_app_key
        self.rss_app_secret = rss_app_secret
        self.user_service = user_service
        self.aisettings_service = aisettings_service
        
        self.min_delay = 1.0
        self.max_delay = 3.0
        self.request_timeout = 30
        self.max_concurrent_requests = 10
        
        self.rss_cache = {}
        self.html_cache = {}
        
        self.common_rss_paths = [
            '/feed', '/rss', '/atom.xml', '/feed.xml', '/rss.xml',
            '/blog/feed', '/news/feed', '/feed/rss', '/feed/atom'
        ]
        self.decorative_classes = {
            'icon', 'logo', 'button', 'badge',
            'app-store', 'google-play', 'download',
            'spinner', 'loader', 'ad', 'banner'
        }
        self.skip_alt_words = {
            'download', 'app store', 'google play', 'get it on',
            'available on', 'button', 'logo', 'badge', 'реклама', 'ad'
        }
        self.decorative_url_parts = {
            '/buttons/', '/badges/', '/logos/',
            '/ads/', '/banners/', '/downloads/',
            '/userpics/', '/avatars/'
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
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:127.0) Gecko/20100101 Firefox/127.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'uk-UA,uk;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://www.google.com/',
            'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Cache-Control': 'max-age=0'
        }
        
        if 'Firefox' in headers['User-Agent']:
            headers.pop('Sec-Ch-Ua', None)
            headers.pop('Sec-Ch-Ua-Mobile', None)
            headers.pop('Sec-Ch-Ua-Platform', None)
        elif 'Safari' in headers['User-Agent']:
            headers.update({
                'Sec-Ch-Ua': '"Safari";v="17"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"'
            })
        
        return {k: str(v) for k, v in headers.items() if k and v is not None}


    async def _random_delay(self):
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

    def _calculate_source_limits(self, sources: List[Dict], limit: int) -> Dict[str, int]:
        source_limits = {}
        base_limit = max(1, limit // len(sources))
        for source in sources:
            source_limits[source['link']] = base_limit
        
        remaining = limit - base_limit * len(sources)
        for source in sources[:remaining]:
            source_limits[source['link']] += 1
        
        return source_limits

    async def get_last_posts(
        self,
        flow: FlowDTO,
        limit: int = 10
    ) -> List[PostDTO]:
        try:
            start_time = time.time()
            self.logger.info("Starting parallel posts processing")
            
            rss_urls = await self._discover_rss_urls_parallel(flow.sources)
            self.logger.info(f"Discovered RSS URLs: {rss_urls}")
            
            if not rss_urls:
                self.logger.warning("No RSS URLs found after all attempts")
                return []
            
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

    async def _discover_rss_urls_parallel(
        self,
        sources: List[Dict],
        max_retries: int = 3
    ) -> List[str]:
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
        try:
            
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
            'domain': domain
        }
        
        if entry.link:
            enriched = await self._parse_web_page(entry.link, flow, post['images'])
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
        user = await self.user_service.get_user_by_flow(flow)
        processor = ChatGPTContentProcessor(
            api_key=self.openai_key,
            flow=flow,
            aisettings_service=self.aisettings_service,
            max_retries=2,
            timeout=30.0
        )
        return await processor.process_batch(texts, user.id)

    async def _parse_web_page(self, url: str, flow: FlowDTO, rss_images) -> Optional[WebPost]:
        try:
            await self._random_delay()
            html = await self._fetch_html(url)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            article = soup.find('article') or soup.find('main') or soup.body
            text = article.get_text(separator='\n', strip=True) if article else ''
            
            if rss_images:
                images = []
            else:
                images = self._extract_quality_images(soup, url)

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
        
    async def _get_rss_via_api(self, url: str, max_retries: int = 2) -> Optional[str]:
        if not url or not isinstance(url, str):
            self.logger.error("Invalid URL provided for RSS API")
            return None

        headers = {
            "Authorization": f"Bearer {self.rss_app_key}:{self.rss_app_secret}",
            "Content-Type": "application/json"
        }
        
        json_data = {"url": str(url)}
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                async with self.session.post(
                    "https://api.rss.app/v1/feeds",
                    headers=headers,
                    json=json_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('rss_feed_url')
                    else:
                        error_text = await response.text()
                        self.logger.error(f"RSS API error {response.status}: {error_text}")
                        if response.status >= 500:
                            continue

            except TypeError as e:
                if "Cannot serialize non-str key None" in str(e):
                    self.logger.warning(f"Attempt {attempt + 1}: Header serialization error, retrying...")
                    headers = {k: str(v) for k, v in headers.items() if v is not None}
                    last_exception = e
                    continue
                raise
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}", exc_info=True)
                last_exception = e
                await asyncio.sleep(1)
                continue

            break

        if last_exception:
            self.logger.error(f"All {max_retries + 1} attempts failed. Last error: {str(last_exception)}")
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
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                
                if response.status == 403:
                    self.logger.warning("Cloudflare detected, using bypass")
                    return await self.cf_bypass.get_page_content(url)
                
        except Exception as e:
            self.logger.error(f"Fetch error: {str(e)}")
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

        desc = getattr(entry, 'description', '')
        if desc:
            soup = BeautifulSoup(desc, "html.parser")
            for img_tag in soup.find_all("img"):
                src = img_tag.get("src")
                if src and not src.endswith(".svg"):
                    images.append(src)

        images = list(dict.fromkeys(images))[:3]
        self.logger.info(f'===IMAGES RSS=== {images}')
        return images

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[datetime]:
        try:
            return date_parser.parse(date_str)
        except Exception:
            return None

    async def close(self):
        await self.session.close()

    def _has_news_caption(self, img_tag) -> bool:
        for parent in img_tag.parents:
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
        
        for img in soup.find_all('img'):
            if img.parent and img.parent.name == 'picture':
                continue
                
            img_url = self._get_image_url(img, base_url)
            if img_url and not self._should_skip_image(img, img_url):
                images.append(img_url)
        
        unique_images = list(dict.fromkeys(images))
        return unique_images[:5]

    def _is_news_image(self, img_url: str) -> bool:
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
        # 1. Absolute exclusions (SVG, inline data URLs, GIFs)
        img_url_lower = img_url.lower()
        if img_url_lower.endswith('.svg') or img_url.startswith('data:') or img_url_lower.endswith('.gif'):
            return True

        # 2. If the image is within a news content block - never skip it
        if self._is_in_news_block(img_tag):
            return False

        # 3. Skip tiny or decorative images (only for non-news images)
        if self._is_tiny_or_decorative(img_tag):
            return True

        # 4. Check by class names (decorative UI elements)

        img_classes = img_tag.get('class', [])
        if isinstance(img_classes, str):
            img_classes = img_classes.split()

        if any(cls in self.decorative_classes for cls in img_classes):
            return True

        # 5. Check by alt text for decorative keywords
        alt_text = img_tag.get('alt', '').lower()

        if any(keyword in alt_text for keyword in self.skip_alt_words):
            return True

        # 6. Check URL path for decorative assets
        if any(part in img_url_lower for part in self.decorative_url_parts):
            return True

        return False


    def _is_tiny_or_decorative(self, img_tag) -> bool:
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
        value = img_tag.get(dimension)
        if not value:
            return None
            
        try:
            if isinstance(value, str):
                value = value.replace('px', '')
            return int(float(value))
        except (ValueError, TypeError):
            return None