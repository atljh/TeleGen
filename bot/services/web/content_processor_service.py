import asyncio
import logging
from bot.database.dtos.dtos import FlowDTO
from bot.services.content_processing.processors import (
    ChatGPTContentProcessor, DefaultContentProcessor
)

class ContentProcessorService:
    def __init__(
        self,
        openai_key: str = None,
        logger: logging.Logger | None = None
    ):
        self.openai_key = openai_key
        self.default_processor = DefaultContentProcessor()
        self.logger = logger or logging.getLogger(__name__)
        
    async def process_batch(
        self,
        texts: list[str],
        flow: FlowDTO,
        user_id: int
    ) -> list[str]:
        if self.openai_key:
            processor = ChatGPTContentProcessor(
                api_key=self.openai_key,
                flow=flow,
                max_retries=2,
                timeout=30.0
            )
            return await processor.process_batch(texts, user_id)
        return await asyncio.gather(*[
            self.default_processor.process(text)
            for text in texts
        ])