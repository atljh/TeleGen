
import asyncio
from datetime import datetime
import logging
from typing import List, Optional
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from bot.database.dtos.dtos import FlowDTO, PostDTO
from bot.services.content_processing.processors import ChatGPTContentProcessor, DefaultContentProcessor

class WebService:
    def __init__(self, openai_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.openai_key = openai_key
        self._semaphore = asyncio.Semaphore(10)

    async def get_last_posts(self, flow: FlowDTO, limit: int = 10) -> List[PostDTO]:
        tasks = []
        for source in flow.sources[:limit]:
            if source['type'] != 'web':
                continue
            tasks.append(self._process_source(source, flow))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, PostDTO)]

    async def _process_source(self, source: dict, flow: FlowDTO) -> Optional[PostDTO]:
        try:
            async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
                result = await crawler.arun(
                    url=source['link'],
                    config=BrowserConfig(enable_js=True, wait_for_page_load=2)
                )

            content = result.markdown or result.cleaned_text or result.raw_html
            if not content:
                return None

            processed_text = await self._process_content(content, flow)

            return PostDTO(
                content=processed_text,
                flow_id=flow.id,
                source_url=source['link'],
                original_link=source['link'],
                original_date=None,
                created_at=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Ошибка при обработке {source['link']}: {str(e)}")
            return None

    async def _process_content(self, text: str, flow: FlowDTO) -> str:
        text = await DefaultContentProcessor().process(text)

        if self.openai_key:
            async with self._semaphore:
                text = await self._process_with_chatgpt(text, flow)

        if flow.signature:
            text = f"{text}\n\n{flow.signature}"

        return text

    async def _process_with_chatgpt(self, text: str, flow: FlowDTO) -> str:
        processor = ChatGPTContentProcessor(
            api_key=self.openai_key,
            flow=flow,
            max_retries=2,
            timeout=15.0
        )
        return await processor.process(text)
