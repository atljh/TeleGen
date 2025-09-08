import asyncio
import logging
from typing import Optional
import openai
from bot.database.models.post import PostDTO
from bot.services.content_processing.processors import (
    ChatGPTContentProcessor,
    DefaultContentProcessor,
)
from bot.services.aisettings_service import AISettingsService
from bot.services.user_service import UserService
from bot.database.models import FlowDTO


class ContentProcessingService:
    def __init__(
        self,
        openai_key: str = None,
        aisettings_service: AISettingsService = None,
        user_service: UserService = None,
    ):
        self.openai_key = openai_key
        self.aisettings_service = aisettings_service
        self.user_service = user_service
        self._openai_client = None
        self._semaphore = asyncio.Semaphore(10)
        self.logger = logging.getLogger(__name__)

    @property
    def openai_client(self):
        if not self._openai_client and self.openai_key:
            self._openai_client = openai.AsyncOpenAI(api_key=self.openai_key)
        return self._openai_client

    async def process_post_content(
        self, post_dto: PostDTO, flow: FlowDTO
    ) -> Optional[PostDTO]:
        if not post_dto.content:
            return None

        normalized_content = await self._normalize_content(post_dto.content)

        processed_content = await self._process_with_ai(normalized_content, flow)

        final_content = await self._add_signature(processed_content, flow)

        return post_dto.copy(update={"content": final_content})

    async def _normalize_content(self, content) -> str:
        if isinstance(content, list):
            content = " ".join(filter(None, content))

        return await DefaultContentProcessor().process(content)

    async def _process_with_ai(self, text: str, flow: FlowDTO) -> str:
        if not self.openai_key:
            return text

        async with self._semaphore:
            return await self._process_with_chatgpt(text, flow)

    async def _process_with_chatgpt(self, text: str, flow: FlowDTO) -> str:
        try:
            user = await self.user_service.get_user_by_flow(flow)
            processor = ChatGPTContentProcessor(
                api_key=self.openai_key,
                flow=flow,
                max_retries=2,
                timeout=15.0,
                aisettings_service=self.aisettings_service,
            )
            return await processor.process(text, user.id)
        except Exception as e:
            self.logger.error(f"ChatGPT processing failed: {str(e)}")
            return text

    async def _add_signature(self, text: str, flow: FlowDTO) -> str:
        if flow.signature:
            return f"{text}\n\n{flow.signature}"
        return text
