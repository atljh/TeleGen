import re
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

import openai

from bot.database.dtos.dtos import FlowDTO


class ContentProcessor(ABC):
    @abstractmethod
    async def process(self, text: str) -> str:
        pass


class DefaultContentProcessor(ContentProcessor):
    def __init__(self):
        self.patterns = {
            'url': re.compile(r'https?://\S+|www\.\S+'),
            'username': re.compile(r'@\w+'),
            'bold_asterisks': re.compile(r'\*\*([^*]+)\*\*'),
            'hidden_chars': re.compile(r'[\u200B-\u200D\uFEFF]'),
            'emoji': re.compile(r'[^\w\s,.!?;:@#%&*+-=]'),
            'markdown_links': re.compile(r'\[([^\]]+)\]\([^)]+\)'),
            'telegram_commands': re.compile(r'/\w+')
        }

    async def process(self, text: str) -> str:
        if not text:
            return ""

        for pattern_name, pattern in self.patterns.items():
            if pattern_name == 'markdown_links':
                text = pattern.sub(r'\1', text)
            else:
                text = pattern.sub('', text)

        text = ' '.join(text.split())
        return text.strip()

class ChatGPTContentProcessor(ContentProcessor):
    def __init__(self, api_key: str, flow: FlowDTO, model: str = "gpt-4-turbo"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.flow = flow
        self.model = model
        self.max_retries = 3

    async def process(self, text: str) -> str:
        logging.info('=======================PROCESS===================')
        if not text.strip():
            return ""

        system_prompt = self._build_system_prompt()
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.5,
                    # max_tokens=self._get_max_tokens(),
                    top_p=0.9
                )
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"ChatGPT processing failed: {str(e)}")
                    return text
                await asyncio.sleep(1.5 * (attempt + 1))  # Exponential backoff

    def _build_system_prompt(self) -> str:
        rules = [
            "Ты профессиональный редактор постов. Обработай текст согласно правилам:",
            "1. Сохрани основной смысл, но сделай текст более читаемым",
            "2. Удали лишние ссылки и спецсимволы",
            # f"3. Длина текста: {self._get_length_instruction()}",
            f"4. Стиль: {self.flow.theme}",
        ]
        
        if self.flow.use_emojis:
            emoji_type = "премиум" if self.flow.use_premium_emojis else "обычные"
            rules.append(f"5. Добавь {emoji_type} emoji (1-2 в начале и 1-2 в конце)")
        
        if self.flow.title_highlight:
            logging.info("6. Выделяю заголовок")
            rules.append("6. Выдели заголовок с помощью emoji или форматирования")
        
        if self.flow.cta:
            rules.append("7. Добавь призыв к действию в конце")
        
        if self.flow.signature:
            rules.append(f"8. В конце добавь подпись: '{self.flow.signature}'")
        
        rules.append("Не добавляй свои комментарии, только обработанный текст")
        return "\n".join(rules)

    # def _get_length_instruction(self) -> str:
    #     lengths = {
    #         "short": "короткий (1-2 предложения)",
    #         "medium": "средний (3-5 предложений)", 
    #         "long": "полный текст (без сокращений)"
    #     }
    #     return lengths.get(self.flow.content_length, "средний (3-5 предложений)")

    # def _get_max_tokens(self) -> int:
    #     return {
    #         "short": 500,
    #         "medium": 1000,
    #         "long": 2000
    #     }.get(self.flow.content_length, 1000)