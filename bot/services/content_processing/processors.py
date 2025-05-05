import re
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

import openai
from langdetect import detect

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
        text = text.replace('_', '')

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

        system_prompt = self._build_system_prompt(text)
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.5,
                    top_p=0.9
                )
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"ChatGPT processing failed: {str(e)}")
                    return text
                await asyncio.sleep(1.5 * (attempt + 1))

    def _build_system_prompt(self, text: str) -> str:
        detected_language = detect(text)
        language_name = {
            'uk': 'Ukrainian',
            'ru': 'Russian',
            'en': 'English'
        }.get(detected_language, 'the original language')

        rules = [
            "You are a professional post editor.",
            f"Do not change the language — keep it in {language_name}. No translation.",
            f"Edit the text according to the following rules:",
            f"1. Keep the original meaning, but improve readability and clarity.",
            f"2. Remove unnecessary links, formatting artifacts, and special characters.",
            f"3. The total text length must not exceed {self._get_length_instruction()} characters.",
            f"4. Rewrite the text in the following style: {self.flow.theme}.",
        ]

        if self.flow.use_emojis:
            emoji_type = "premium" if self.flow.use_premium_emojis else "regular"
            rules.append(f"5. Insert appropriate {emoji_type} emojis into the text where relevant.")
        
        if self.flow.title_highlight:
            logging.info("6. Highlighting the title")
            rules.append("6. Highlight the title using the <b> HTML tag.")
        
        if self.flow.cta:
            logging.info("7. Adding call to action")
            rules.append("7. Add a concise and relevant call to action at the end of the post.")
        
        if self.flow.signature:
            logging.info(f"8. Adding signature: '{self.flow.signature}'")
            rules.append(f"8. Append the following signature at the end of the post: '{self.flow.signature}'.")
        
        rules.append("Return only the edited post. Do not include any explanations or extra commentary.")
        return "\n".join(rules)

    def _get_length_instruction(self) -> str:
        lengths = {
            "short": "100",
            "medium": "300", 
            "long": "1000"
        }
        logging.info(self.flow.content_length)
        return lengths.get(self.flow.content_length, "300")
