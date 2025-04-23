import re
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

import openai


class ContentProcessor(ABC):
    @abstractmethod
    async def process(self, text: str) -> str:
        """Основной метод обработки текста"""
        pass


class DefaultContentProcessor(ContentProcessor):
    def __init__(self):
        self.link_regex = re.compile(r'https?://\S+|www\.\S+')
        self.special_chars_regex = re.compile(r'[\u200B-\u200D\uFEFF]')

    async def process(self, text: str) -> str:
        if not text.strip():
            return ""
        
        text = self.special_chars_regex.sub('', text)
        
        text = self.link_regex.sub('', text)
        
        return ' '.join(text.split()).strip()


class ChatGPTContentProcessor(ContentProcessor):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_retries = 3

    async def process(self, text: str) -> str:
        if not text.strip():
            return ""

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Ты помощник для обработки постов. Удали лишние ссылки, "
                                "спецсимволы, улучши читаемость, сохранив смысл. "
                                "Не добавляй комментарии от себя."
                            )
                        },
                        {"role": "user", "content": text}
                    ],
                    temperature=0.5,
                    max_tokens=2000
                )
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"ChatGPT error after {self.max_retries} attempts: {str(e)}")
                    return text
                await asyncio.sleep(1)