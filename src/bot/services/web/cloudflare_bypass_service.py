import asyncio
import time

import cloudscraper


class CloudflareBypass:
    def __init__(self, logger):
        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True},
            delay=10,
            interpreter="nodejs",
        )
        self.logger = logger
        self.success_count = 0
        self.fail_count = 0

    async def fetch_with_cloudscraper(self, url: str) -> str | None:
        try:
            resp = await asyncio.to_thread(self.scraper.get, url)
            if resp.status_code == 200:
                return resp.text
            self.logger.warning(f"CloudScraper failed with status {resp.status_code}")
        except Exception as e:
            self.logger.error(f"CloudScraper error: {e!s}")
        return None

    async def _try_methods(self, url: str) -> str | None:
        content = await self.fetch_with_cloudscraper(url)
        if content:
            return content

        self.logger.warning("CloudScraper failed, Selenium is disabled")
        return None

    async def get_page_content(self, url: str) -> str | None:
        start_time = time.time()
        try:
            result = await self._try_methods(url)
            if result:
                self.success_count += 1
                self.logger.info(f"Success (took {time.time()-start_time:.2f}s)")
            else:
                self.fail_count += 1
            return result
        except Exception as e:
            self.logger.error(f"Critical error: {e!s}")
            return None
