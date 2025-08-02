import asyncio
import hashlib
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from pydantic import BaseModel

from bot.services.cloudflare_bypass_service import CloudflareBypass

class RssPost(BaseModel):
    title: str
    content: str
    date: Optional[datetime]
    source_url: str
    original_link: str
    images: List[str]
    domain: str
    source_id: str


class RssService:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.cf_bypass = CloudflareBypass(self.logger)
        
        self.min_delay = 1.0
        self.max_delay = 3.0
        self.request_timeout = 30
        self.common_rss_paths = [
            '/feed', '/rss', '/atom.xml', '/feed.xml', '/rss.xml',
            '/blog/feed', '/news/feed', '/feed/rss', '/feed/atom'
        ]
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.request_timeout),
            headers=self._generate_headers()
        )

    async def discover_rss_urls(self, sources: List[Dict]) -> List[str]:
        tasks = [self._discover_rss_for_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [url for url in results if url and not isinstance(url, Exception)]

    async def fetch_posts(self, rss_urls: List[str], limit: int = 10) -> List[RssPost]:
        limits_per_url = self._calculate_limits_per_url(rss_urls, limit)
        tasks = [self._fetch_feed_posts(url, limits_per_url[url]) for url in rss_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [post for sublist in results if not isinstance(sublist, Exception) for post in sublist]

    async def close(self):
        await self.session.close()

    async def _discover_rss_for_source(self, source: Dict) -> Optional[str]:
        base_url = source['link'].rstrip('/')
        
        for path in self.common_rss_paths:
            rss_url = f"{base_url}{path}"
            if await self._validate_rss_feed(rss_url):
                return rss_url
        
        if hasattr(self, 'rss_app_key') and hasattr(self, 'rss_app_secret'):
            return await self._get_rss_via_api(base_url)
        
        return None

    async def _fetch_feed_posts(self, rss_url: str, limit: int) -> List[RssPost]:
        try:
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    return []
                
                text = await response.text()
                feed = feedparser.parse(text)
                domain = urlparse(rss_url).netloc
                
                return await asyncio.gather(*[
                    self._parse_rss_entry(entry, domain, rss_url)
                    for entry in feed.entries[:limit]
                ])
        except Exception as e:
            self.logger.error(f"Error parsing RSS feed {rss_url}: {str(e)}")
            return []

    async def _parse_rss_entry(self, entry, domain: str, rss_url: str) -> RssPost:
        await self._random_delay()
        
        return RssPost(
            title=entry.title,
            content=getattr(entry, 'description', None) or getattr(entry, 'summary', None) or entry.title,
            original_link=entry.link,
            original_date=self._parse_rss_date(entry.get('published')),
            source_url=rss_url,
            source_id=f"rss_{hashlib.md5(entry.link.encode()).hexdigest()}",
            images=self._extract_rss_images(entry),
            domain=domain
        )

    def _extract_rss_images(self, entry) -> List[str]:
        images = []
        
        if hasattr(entry, 'media_content'):
            images.extend(media.get('url') for media in entry.media_content 
                        if media.get('type', '').startswith('image/'))
        
        if hasattr(entry, 'links'):
            images.extend(link.get('href') for link in entry.links 
                        if link.get('type', '').startswith('image/'))
        
        if hasattr(entry, 'description'):
            soup = BeautifulSoup(entry.description, "html.parser")
            images.extend(img.get("src") for img in soup.find_all("img"))
        
        return list({
            url for url in images 
            if url and not url.endswith('.svg') and self._is_valid_image_url(url)
        })[:3]

    async def _validate_rss_feed(self, url: str) -> bool:
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return False
                
                text = await response.text()
                feed = feedparser.parse(text)
                return len(feed.entries) > 0
        except Exception:
            return False

    def _calculate_limits_per_url(self, urls: List[str], total_limit: int) -> Dict[str, int]:
        base_limit = total_limit // len(urls)
        extra = total_limit % len(urls)
        return {url: base_limit + (1 if i < extra else 0) for i, url in enumerate(urls)}

    def _parse_rss_date(self, date_str: Optional[str]) -> Optional[datetime]:
        try:
            return date_parser.parse(date_str) if date_str else None
        except Exception:
            return None

    def _is_valid_image_url(self, url: str) -> bool:
        if not url:
            return False
        
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp'])

    def _generate_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

    async def _random_delay(self):
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))