import logging
from datetime import datetime
from typing import Self
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

from bot.database.models.web_post import WebPost
from bot.services.web.cloudflare_bypass_service import CloudflareBypass


class WebScraperService:
    def __init__(
        self, cf_bypass: CloudflareBypass, logger: logging.Logger | None = None
    ) -> None:
        self.cf_bypass = cf_bypass
        self.session = aiohttp.ClientSession()
        self.logger = logger or logging.getLogger(__name__)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    async def scrape_page(self, url: str) -> WebPost | None:
        """
        Scrape web page and return structured data.

        Args:
            url: URL of the page to scrape

        Returns:
            WebPost if successful, None otherwise
        """
        try:
            html = await self._fetch_html(url)
            if not html:
                return None

            soup = BeautifulSoup(html, "html.parser")
            article = self._find_main_content(soup)

            return WebPost(
                title=self._get_title(soup, url),
                content=self._extract_text(article),
                url=url,
                source=urlparse(url).netloc,
                date=self._find_publication_date(soup),
            )
        except Exception as e:
            self.logger.error(f"Scraping error for {url}: {e!s}", exc_info=True)
            return None

    async def close(self) -> None:
        await self.session.close()

    async def _fetch_html(self, url: str) -> str | None:
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                if response.status == 403:
                    self.logger.warning(f"Cloudflare detected on {url}, using bypass")
                    return await self.cf_bypass.get_page_content(url)
                self.logger.warning(f"Unexpected status {response.status} for {url}")
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e!s}")
        return None

    def _find_main_content(self, soup: BeautifulSoup) -> BeautifulSoup | None:
        return (
            soup.find("article")
            or soup.find("main")
            or soup.find(class_="main-content")
            or soup.body
        )

    def _get_title(self, soup: BeautifulSoup, fallback: str) -> str:
        return (
            soup.title.string
            or soup.find("meta", property="og:title")["content"]
            or fallback
        )

    def _extract_text(self, element: BeautifulSoup | None) -> str:
        return element.get_text(separator="\n", strip=True) if element else ""

    def _find_publication_date(self, soup: BeautifulSoup) -> datetime | None:
        for meta in soup.find_all("meta"):
            if meta.get("property") in ("article:published_time", "date"):
                try:
                    return datetime.fromisoformat(meta["content"])
                except (ValueError, KeyError):
                    continue
        return None
