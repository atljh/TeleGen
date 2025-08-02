import asyncio
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel

from bot.database.dtos.dtos import FlowDTO, PostDTO, PostImageDTO, PostStatus
from bot.services.cloudflare_bypass_service import CloudflareBypass
from bot.services.content_processing.processors import ChatGPTContentProcessor, DefaultContentProcessor
from bot.services.aisettings_service import AISettingsService
from bot.services.user_service import UserService
from bot.services.flow_service import FlowService
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
        rss_service,
        aisettings_service: AISettingsService,
        user_service: UserService,
        flow_service: FlowService,
        openai_key: str = None
    ):
        self.logger = logging.getLogger(__name__)
        self.cf_bypass = CloudflareBypass(self.logger)
        self.rss_service = rss_service
        self.openai_key = openai_key
        self.user_service = user_service
        self.aisettings_service = aisettings_service
        self.flow_service = flow_service

        self.min_delay = 1.0
        self.max_delay = 3.0
        self.request_timeout = 30
        
        self.html_cache = {}
        
        self.decorative_classes = {
            'icon', 'logo', 'button', 'badge',
            'app-store', 'google-play', 'download',
            'spinner', 'loader', 'ad', 'banner',
            'block_texts__content'
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
        self.sponsor_indicators = {
            'sponsor', 'partner', 'supported-by', 
            'sponsored', 'presented-by', 'powered-by'
        }
        self.min_news_image_size = (400, 250)

        self.session = aiohttp.ClientSession(
            headers=self._generate_headers(),
            timeout=aiohttp.ClientTimeout(total=self.request_timeout)
        )

    async def get_last_posts(
        self,
        flow: FlowDTO,
        limit: int = 10
    ) -> List[PostDTO]:
        try:
            start_time = time.time()
            self.logger.info("Starting posts processing")
            
            # Get raw posts from RSS service
            raw_posts = await self.rss_service.get_posts_for_flow(flow, limit)
            
            # Enrich with web data
            enriched_posts = await self._enrich_posts_with_web_data(raw_posts, flow)
            
            # Process content
            processed_posts = await self._process_posts_batch(enriched_posts, flow)
            
            self.logger.info(
                f"Processed {len(processed_posts)} posts in {time.time() - start_time:.2f}s"
            )
            return processed_posts[:limit]
        except Exception as e:
            self.logger.error(f"Error in get_last_posts: {str(e)}", exc_info=True)
            return []

    async def _enrich_posts_with_web_data(
        self, 
        raw_posts: List[Dict],
        flow: FlowDTO
    ) -> List[Dict]:
        """Enhance RSS posts with additional web data"""
        tasks = []
        for post in raw_posts:
            if post.get('original_link'):
                tasks.append(self._enrich_single_post(post, flow))
            else:
                tasks.append(post)
        
        return await asyncio.gather(*tasks)

    async def _enrich_single_post(
        self,
        post: Dict,
        flow: FlowDTO
    ) -> Dict:
        """Enrich single post with web page data"""
        try:
            enriched = await self._parse_web_page(post['original_link'], flow, post.get('images', []))
            if enriched:
                combined_images = list(
                    {img: None for img in post.get('images', []) + (enriched.images or [])}.keys()
                )
                return {
                    **post,
                    'content': enriched.content or post['content'],
                    'images': combined_images[:5]
                }
        except Exception as e:
            self.logger.error(f"Error enriching post {post['original_link']}: {str(e)}")
        
        return post

    async def _parse_web_page(
        self, 
        url: str, 
        flow: FlowDTO, 
        existing_images: List[str] = None
    ) -> Optional[WebPost]:
        """Parse web page to extract additional content"""
        try:
            await self._random_delay()
            html = await self._fetch_html(url)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            article = soup.find('article') or soup.find('main') or soup.body
            text = article.get_text(separator='\n', strip=True) if article else ''
            
            images = []
            if not existing_images:
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

    async def _process_posts_batch(
        self, 
        raw_posts: List[Dict], 
        flow: FlowDTO
    ) -> List[PostDTO]:
        """Process batch of posts through content processors"""
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

    async def _process_with_chatgpt_batch(
        self, 
        texts: List[str], 
        flow: FlowDTO
    ) -> List[str]:
        """Process texts with ChatGPT in batch"""
        user = await self.user_service.get_user_by_flow(flow)
        processor = ChatGPTContentProcessor(
            api_key=self.openai_key,
            flow=flow,
            aisettings_service=self.aisettings_service,
            max_retries=2,
            timeout=30.0
        )
        return await processor.process_batch(texts, user.id)

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                
                if response.status == 403:
                    self.logger.warning("Cloudflare detected, using bypass")
                    return await self.cf_bypass.get_page_content(url)
                
        except Exception as e:
            self.logger.error(f"Fetch error for {url}: {str(e)}")
        return None

    def _extract_quality_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract high-quality relevant images from page"""
        images = []
        domain = urlparse(base_url).netloc

        for picture in soup.find_all('picture'):
            img = picture.find('img', src=True)
            if img:
                img_url = self._get_image_url(img, base_url)
                if self._is_sponsor_image(img, domain):
                    continue
                if img_url and not self._should_skip_image(img, img_url):
                    self.logger.debug(f"Adding news image: {img_url}")
                    return [img_url]

        for img in soup.find_all('img'):
            if img.parent and img.parent.name == 'picture':
                continue

            img_url = self._get_image_url(img, base_url)
            if img_url and not self._should_skip_image(img, img_url):
                return [img_url]

        return []

    def _is_sponsor_image(self, img_tag, domain: str) -> bool:
        """Check if image is sponsored content"""
        domain_rules = {
            'pgatour.com': {
                'url_patterns': ['/temp/legendSponsors/'],
                'class_patterns': ['legendSponsors']
            }
        }
        
        if domain in domain_rules:
            rules = domain_rules[domain]
            img_url = self._get_image_url(img_tag, '')
            
            if img_url and any(pattern in img_url for pattern in rules['url_patterns']):
                return True
                
            classes = img_tag.get('class', [])
            if isinstance(classes, str):
                classes = classes.split()
                
            if any(pattern in ' '.join(classes) for pattern in rules['class_patterns']):
                return True
        
        return False

    def _should_skip_image(self, img_tag, img_url: str) -> bool:
        """Determine if image should be skipped"""
        img_url_lower = img_url.lower()
        if img_url_lower.endswith('.svg') or img_url.startswith('data:') or img_url_lower.endswith('.gif'):
            return True

        if self._is_in_news_block(img_tag):
            return False

        if self._is_tiny_or_decorative(img_tag):
            return True

        img_classes = img_tag.get('class', [])
        if isinstance(img_classes, str):
            img_classes = img_classes.split()

        if any(cls in self.decorative_classes for cls in img_classes):
            return True

        alt_text = img_tag.get('alt', '').lower()
        if any(keyword in alt_text for keyword in self.skip_alt_words):
            return True

        if any(part in img_url_lower for part in self.decorative_url_parts):
            return True

        alt_text = img_tag.get('alt', '').lower()
        if any(keyword in alt_text for keyword in self.sponsor_indicators):
            return True
            
        for parent in img_tag.parents:
            parent_classes = parent.get('class', [])
            if isinstance(parent_classes, str):
                parent_classes = parent_classes.split()
                
            if any(indicator in ' '.join(parent_classes).lower() 
                for indicator in self.sponsor_indicators):
                return True
                
        if any(indicator in img_url.lower() 
            for indicator in self.sponsor_indicators):
            return True

        return False

    def _is_in_news_block(self, img_tag) -> bool:
        """Check if image is in news content block"""
        for parent in img_tag.parents:
            parent_classes = parent.get('class', [])
            if isinstance(parent_classes, str):
                parent_classes = parent_classes.split()
            
            if any(cls in self.news_block_classes for cls in parent_classes):
                return True
            
            if parent.name == 'div' and any(
                sibling.name in ['div', 'figcaption'] and 
                any(cls in ['caption', 'source', 'credit'] 
                    for cls in sibling.get('class', []))
                for sibling in parent.find_next_siblings()
            ):
                return True
        
        return False

    def _is_tiny_or_decorative(self, img_tag) -> bool:
        """Check if image is too small or decorative"""
        if self._is_in_news_block(img_tag):
            return False
        
        width = self._get_image_dimension(img_tag, 'width')
        height = self._get_image_dimension(img_tag, 'height')
        
        min_news_width = 400
        min_news_height = 250
        
        if not width or not height:
            return False
        
        if width < min_news_width or height < min_news_height:
            return True
        
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

    def _get_image_url(self, img_tag, base_url: str) -> Optional[str]:
        """Extract image URL from img tag"""
        for attr in ['data-src', 'src', 'data-original', 'data-srcset']:
            img_url = img_tag.get(attr)
            if img_url:
                if attr == 'data-srcset':
                    img_url = img_url.split(',')[0].split()[0]
                return self._normalize_image_url(img_url, base_url)
        return None

    def _normalize_image_url(self, img_url: str, base_url: str) -> str:
        """Convert relative URLs to absolute"""
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
        """Get image dimension from tag attributes"""
        value = img_tag.get(dimension)
        if not value:
            return None
            
        try:
            if isinstance(value, str):
                value = value.replace('px', '')
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _generate_headers(self) -> Dict[str, str]:
        """Generate random request headers"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'uk-UA,uk;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6',
            'Referer': 'https://www.google.com/'
        }

    async def _random_delay(self):
        """Random delay between requests"""
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

    async def close(self):
        """Cleanup resources"""
        await self.session.close()