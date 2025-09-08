import time
from typing import Optional
import asyncio
import cloudscraper
import undetected_chromedriver as uc


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

    async def fetch_with_cloudscraper(self, url: str) -> Optional[str]:
        try:
            resp = await asyncio.to_thread(self.scraper.get, url)
            if resp.status_code == 200:
                return resp.text
            self.logger.warning(f"CloudScraper failed with status {resp.status_code}")
        except Exception as e:
            self.logger.error(f"CloudScraper error: {str(e)}")
        return None

    async def fetch_with_selenium(self, url: str) -> Optional[str]:
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")

        driver = None
        try:
            driver = uc.Chrome(options=options, headless=True, use_subprocess=False)
            driver.get(url)

            await asyncio.sleep(5)

            if "Checking your browser" in driver.page_source:
                self.logger.info("Solving Cloudflare challenge...")
                await asyncio.sleep(10)

            if "Just a moment" not in driver.page_source:
                return driver.page_source

        except Exception as e:
            self.logger.error(f"Selenium error: {str(e)}")
        finally:
            if driver:
                driver.quit()
        return None

    async def _try_methods(self, url: str) -> Optional[str]:
        content = await self.fetch_with_cloudscraper(url)
        if content:
            return content

        self.logger.warning("CloudScraper failed, falling back to Selenium")
        return await self.fetch_with_selenium(url)

    async def get_page_content(self, url: str) -> Optional[str]:
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
            self.logger.error(f"Critical error: {str(e)}")
            return None
