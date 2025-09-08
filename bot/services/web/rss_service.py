from __future__ import annotations

import asyncio
import hashlib
import logging
import random
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Optional, TypedDict
from urllib.parse import urlparse

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from pydantic import BaseModel, ConfigDict, Field

from bot.database.models import FlowDTO
from bot.database.repositories.post_repository import PostRepository
from bot.services.web.cloudflare_bypass_service import CloudflareBypass
from bot.utils.notifications import notify_admins


class SourceDict(TypedDict):
    link: str
    type: str
    rss_url: str


class RssPost(BaseModel):
    title: str = Field(..., min_length=1)
    content: str
    original_date: datetime | None = None
    source_url: str = Field(..., pattern=r"^https?://")
    original_link: str = Field(..., pattern=r"^https?://")
    images: list[str] = Field(default_factory=list)
    domain: str
    source_id: str

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True, extra="forbid")


class RssService:
    def __init__(
        self,
        rss_app_key: str | None = None,
        rss_app_secret: str | None = None,
        post_repository: PostRepository | None = None,
        *,
        logger: logging.Logger | None = None,
        request_timeout: int = 30,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        max_retries: int = 3,
    ):
        self.rss_app_key = rss_app_key
        self.rss_app_secret = rss_app_secret
        self.base_url = "https://api.rss.app/v1"
        self.logger = logger or logging.getLogger(__name__)
        self.cf_bypass = CloudflareBypass(self.logger)
        self.request_timeout = request_timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.post_repository = post_repository

        self.common_rss_paths = [
            "/feed",
            "/rss",
            "/atom.xml",
            "/feed.xml",
            "/rss.xml",
            "/blog/feed",
            "/news/feed",
            "/feed/rss",
            "/feed/atom",
        ]

        self.headers = {
            "Authorization": f"Bearer {self.rss_app_key}:{self.rss_app_secret}",
            "Content-Type": "application/json",
        }
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.request_timeout),
                headers=self._generate_headers(),
            )
        return self._session

    def is_configured(self) -> bool:
        return bool(self.rss_app_key and self.rss_app_secret)

    async def get_posts_for_flow(
        self,
        flow: FlowDTO,
        flow_service: "FlowService",
        limit: int = 10,
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            rss_urls = await self._get_flow_rss_urls(flow, flow_service)

            async for post in self._stream_posts(rss_urls, limit):
                yield self._convert_to_web_service_format(post)

        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout getting posts for flow {flow.id}")
        except Exception as e:
            self.logger.error(f"Error getting posts: {e}", exc_info=True)

    async def _get_flow_rss_urls(
        self, flow: FlowDTO, flow_service: "FlowService"
    ) -> list[str]:
        rss_urls = []
        for source in flow.sources:
            if source["type"] != "web":
                continue
            try:
                if url := await flow_service.get_or_set_source_rss_url(
                    flow.id, source["link"]
                ):
                    rss_urls.append(url)
            except Exception as e:
                self.logger.warning(
                    f"Failed to get RSS URL for source {source.get('link')}: {e}"
                )
        return rss_urls

    async def discover_rss_urls(
        self, sources: list[SourceDict], *, parallel: bool = True
    ) -> list[str]:
        tasks = [self._discover_rss_for_source(source) for source in sources]

        if parallel:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [url for url in results if url and not isinstance(url, Exception)]

        return [await task for task in tasks]

    async def fetch_posts(self, rss_urls: list[str], limit: int = 10) -> list[RssPost]:
        if not rss_urls:
            return []

        try:
            limits_per_url = self._calculate_limits_per_url(rss_urls, limit)
            tasks = [
                self._fetch_feed_posts(url, limits_per_url[url]) for url in rss_urls
            ]
            async with asyncio.timeout(30):
                results = await asyncio.gather(*tasks, return_exceptions=True)
            return [
                post
                for sublist in results
                if not isinstance(sublist, Exception)
                for post in sublist
            ]

        except asyncio.TimeoutError:
            self.logger.warning("Timeout while fetching posts")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching posts: {e}")
            return []

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> RssService:
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    async def _stream_posts(
        self,
        rss_urls: list[str],
        limit: int,
    ) -> AsyncIterator[RssPost]:
        if not rss_urls:
            return

        limits_per_url = self._calculate_limits_per_url(rss_urls, limit)
        for url, url_limit in limits_per_url.items():
            try:
                async with asyncio.timeout(30):
                    async for post in self._fetch_feed_posts_stream(url, url_limit):
                        yield post
            except Exception as e:
                self.logger.warning(f"Error streaming posts from {url}: {e}")

    async def _fetch_feed_posts_stream(
        self,
        rss_url: str,
        limit: int,
    ) -> AsyncIterator[RssPost]:
        try:
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    return

                text = await asyncio.wait_for(response.text())
                feed = feedparser.parse(text)
                domain = urlparse(rss_url).netloc

                for entry in feed.entries[:limit]:
                    try:
                        yield await self._parse_rss_entry(entry, domain, rss_url)
                    except Exception as e:
                        self.logger.warning(f"Error parsing entry: {e}")

        except Exception as e:
            self.logger.error(f"Error fetching feed {rss_url}: {e}")
            raise

    def _convert_to_web_service_format(self, post: RssPost) -> dict[str, Any]:
        if post:
            return {
                "title": post.title,
                "content": post.content,
                "original_link": post.original_link,
                "original_date": post.original_date,
                "source_url": post.source_url,
                "source_id": post.source_id,
                "images": post.images,
                "domain": post.domain,
            }

    async def _discover_rss_for_source(
        self, source: SourceDict, *, retry: int = 0
    ) -> str | None:
        base_url = source["link"].rstrip("/")

        try:
            # for path in self.common_rss_paths:
            #     rss_url = f"{base_url}{path}"
            #     if await self._validate_rss_feed(rss_url):
            #         return rss_url

            if self.rss_app_key and self.rss_app_secret:
                return await self._get_rss_via_api(base_url)

            return None

        except Exception as e:
            if retry < self.max_retries:
                await asyncio.sleep(1 + retry * 2)
                return await self._discover_rss_for_source(source, retry=retry + 1)
            self.logger.warning(
                f"Failed to discover RSS for {base_url} after {retry} retries: {e}"
            )
            return None

    async def _fetch_feed_posts(
        self,
        rss_url: str,
        limit: int,
        *,
        retry: int = 0,
    ) -> list[RssPost]:
        try:
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    return []

                text = await response.text()
                feed = feedparser.parse(text)
                domain = urlparse(rss_url).netloc

                return await asyncio.gather(
                    *[
                        self._parse_rss_entry(entry, domain, rss_url)
                        for entry in feed.entries[:limit]
                    ]
                )
        except Exception as e:
            if retry < self.max_retries:
                await asyncio.sleep(1 + retry * 2)
                return await self._fetch_feed_posts(rss_url, limit, retry=retry + 1)
            self.logger.error(
                f"Failed to fetch posts from {rss_url} after {retry} retries: {e}"
            )
            return []

    async def _parse_rss_entry(
        self,
        entry: feedparser.FeedParserDict,
        domain: str,
        rss_url: str,
    ) -> Optional[RssPost]:
        await self._random_delay()

        try:
            source_id = f"rss_{hashlib.md5(entry.link.encode()).hexdigest()}"

            if await self.post_repository._post_exists(source_id=source_id):
                self.logger.debug(f"STOP | Post already exists: {source_id}")
                return None

            post_data = {
                "title": entry.title,
                "content": getattr(entry, "description", "")
                or getattr(entry, "summary", "")
                or entry.title,
                "original_link": entry.link,
                "original_date": self._parse_rss_date(entry.get("published")),
                "source_url": rss_url,
                "source_id": source_id,
                "images": self._extract_rss_images(entry),
                "domain": domain,
            }
            return RssPost(**post_data)

        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {e}", exc_info=True)
            return None

    def _extract_rss_images(self, entry: feedparser.FeedParserDict) -> list[str]:
        images: set[str] = set()

        # 1. Проверка media_content (стандартный способ)
        if hasattr(entry, "media_content"):
            images.update(
                media["url"]
                for media in entry.media_content
                if media.get("medium") == "image"
                or media.get("type", "").startswith("image/")
            )

        # 2. Проверка links
        if hasattr(entry, "links"):
            images.update(
                link["href"]
                for link in entry.links
                if link.get("type", "").startswith("image/")
            )

        # 3. Проверка media_thumbnail (если есть)
        if hasattr(entry, "media_thumbnail"):
            images.update(
                thumb["url"] for thumb in entry.media_thumbnail if thumb.get("url")
            )

        # 4. Проверка описания (HTML парсинг)
        if hasattr(entry, "description"):
            soup = BeautifulSoup(entry.description, "html.parser")
            images.update(img["src"] for img in soup.find_all("img", src=True))

        # 5. Дополнительная проверка для media:content
        if hasattr(entry, "enclosures"):
            images.update(
                enc["href"]
                for enc in entry.enclosures
                if enc.get("type", "").startswith("image/")
            )

        return sorted(
            url
            for url in images
            if url and not url.endswith(".svg") and self._is_valid_image_url(url)
        )[:3]

    async def _validate_rss_feed(self, url: str) -> bool:
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return False

                text = await response.text()
                feed = feedparser.parse(text)
                return bool(feed.entries)
        except Exception:
            return False

    def _calculate_limits_per_url(
        self, urls: list[str], total_limit: int
    ) -> dict[str, int]:
        if not urls:
            return {}

        base_limit = total_limit // len(urls)
        extra = total_limit % len(urls)
        return {url: base_limit + (1 if i < extra else 0) for i, url in enumerate(urls)}

    def _parse_rss_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            return date_parser.parse(date_str)
        except (ValueError, TypeError):
            return None

    def _is_valid_image_url(self, url: str) -> bool:
        if not url:
            return False

        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False

            path = parsed.path.lower()

            valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
            if any(path.endswith(ext) for ext in valid_extensions):
                return True

            image_paths = {
                "/media/",
                "/images/",
                "/img/",
                "/photo/",
                "/wp-content/uploads/",
            }
            if any(img_path in path for img_path in image_paths):
                return True

            cdn_domains = {"cdn.", "images.", "img.", "media."}
            if any(domain in parsed.netloc for domain in cdn_domains):
                return True

            return False
        except Exception:
            return False

    def _generate_headers(self) -> dict[str, str]:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:127.0) Gecko/20100101 Firefox/127.0",
        ]

        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _random_delay(self) -> None:
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

    async def _get_rss_via_api(self, url: str, max_retries: int = 2) -> str | None:
        if not self._validate_api_url(url):
            return None

        for attempt in range(1, max_retries + 2):
            try:
                return await self._make_api_request(url, attempt)
            except Exception as e:
                last_error = e
                if attempt <= max_retries:
                    await self._handle_api_error(e, url, attempt)
                    continue
                break

        self.logger.error(
            f"All {max_retries + 1} attempts failed for {url}. Last error: {str(last_error)}"
        )
        return None

    def _validate_api_url(self, url: str) -> bool:
        if not url or not isinstance(url, str):
            self.logger.error("Invalid URL provided for RSS API")
            return False
        return True

    async def _make_api_request(self, url: str, attempt: int) -> str | None:
        await self._random_delay()

        async with self.session.post(
            "https://api.rss.app/v1/feeds",
            headers=self._prepare_api_headers(self.headers),
            json={"url": url},
            timeout=10,
        ) as response:
            return await self._process_api_response(response, url)

    def _prepare_api_headers(self, headers: dict) -> dict:
        return {k: str(v) for k, v in headers.items() if v is not None}

    async def _process_api_response(
        self, response: aiohttp.ClientResponse, url: str
    ) -> str | None:
        if response.status == 200:
            data = await response.json()
            return data.get("rss_feed_url")

        error_data = await self._parse_api_error(response)
        await self._notify_api_error(response.status, error_data, url)

        if response.status >= 500:
            raise Exception(f"Server error: {response.status}")
        return None

    async def _parse_api_error(self, response: aiohttp.ClientResponse) -> dict:
        try:
            return await response.json()
        except Exception:
            return {"message": "Failed to parse error response"}

    async def _notify_api_error(self, status: int, error_data: dict, url: str) -> None:
        error_message = (
            "🚨 *RSS Feed Creation Failed* 🚨\n"
            f"🔻 *URL:* `{url}`\n"
            f"🔻 *Status Code:* `{status}`\n"
            f"🔻 *Error Type:* `{error_data.get('error', 'Unknown')}`\n"
            f"🔻 *Message:* _{error_data.get('message', 'No details')}_\n\n"
            f"💡 *Details:*\n"
            f"```\n{error_data.get('errors', [{}])[0].get('title', 'No details')}\n```"
        )
        await notify_admins(error_message, parse_mode="Markdown")

    async def _handle_api_error(self, error: Exception, url: str, attempt: int) -> None:
        error_msg = str(error)
        if "Cannot serialize non-str key None" in error_msg:
            self.logger.warning(
                f"Attempt {attempt}: Header serialization error for {url}"
            )
        else:
            self.logger.error(
                f"Attempt {attempt} failed for {url}: {error_msg}", exc_info=True
            )
        await asyncio.sleep(attempt * 2)

    async def delete_feed_by_url(self, rss_url: str) -> bool:
        """
        Delete RSS feed by URL
        Returns True if succesfully deleter or feed not found
        """
        if not self.is_configured():
            self.logger.warning("RSS service not configured - skipping feed deletion")
            return True

        try:
            feed_id = await self._find_feed_id_by_url(rss_url)
            if not feed_id:
                self.logger.info(f"RSS feed not found for URL: {rss_url}")
                return True
            await asyncio.sleep(2)
            return await self._delete_feed(feed_id)

        except Exception as e:
            self.logger.error(f"Error deleting RSS feed {rss_url}: {str(e)}")
            return False

    async def _find_feed_id_by_url(self, rss_url: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                page = 1
                while True:
                    url = f"{self.base_url}/feeds?page={page}&limit=100"

                    async with session.get(url, headers=self.headers) as response:
                        if response.status != 200:
                            self.logger.error(
                                f"Failed to fetch feeds: {response.status}"
                            )
                            return None

                        data = await response.json()
                        feeds = data.get("data", [])
                        if not feeds:
                            return None

                        for feed in feeds:
                            feed_url = feed.get("rss_feed_url", "")
                            if feed_url == rss_url:
                                return feed.get("id")

                        if len(feeds) < 100:
                            return None

                        page += 1

        except Exception as e:
            self.logger.error(f"Error searching for feed: {str(e)}")
            return None

    async def _delete_feed(self, feed_id: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/feeds/{feed_id}"

                async with session.delete(url, headers=self.headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Successfully deleted RSS feed: {feed_id}")
                        return True
                    elif response.status == 404:
                        self.logger.info(
                            f"RSS feed not found (already deleted?): {feed_id}"
                        )
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Failed to delete RSS feed {feed_id}: {response.status} - {error_text}"
                        )
                        return False

        except Exception as e:
            self.logger.error(f"Error deleting feed {feed_id}: {str(e)}")
            return False

    async def create_feed(self, source_url: str) -> Optional[dict]:
        if not self.is_configured():
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/feeds"
                payload = {"url": source_url, "format": "json"}

                async with session.post(
                    url, headers=self.headers, json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return data.get("data")
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Failed to create RSS feed: {response.status} - {error_text}"
                        )
                        return None

        except Exception as e:
            self.logger.error(f"Error creating RSS feed: {str(e)}")
            return None

    async def get_all_feeds(self) -> list[dict]:
        if not self.is_configured():
            return []

        try:
            all_feeds = []
            page = 1

            async with aiohttp.ClientSession() as session:
                while True:
                    url = f"{self.base_url}/feeds?page={page}&limit=100"

                    async with session.get(url, headers=self.headers) as response:
                        if response.status != 200:
                            break

                        data = await response.json()
                        feeds = data.get("data", [])

                        if not feeds:
                            break

                        all_feeds.extend(feeds)

                        if len(feeds) < 100:
                            break

                        page += 1

            return all_feeds

        except Exception as e:
            self.logger.error(f"Error fetching feeds: {str(e)}")
            return []
