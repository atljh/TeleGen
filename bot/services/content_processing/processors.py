import re
import time
import asyncio
import logging
from abc import ABC, abstractmethod

import openai
from langdetect import detect
from psycopg.errors import UniqueViolation

from bot.database.dtos.dtos import FlowDTO
from bot.database.exceptions import AISettingsNotFoundError
from bot.services.aisettings_service import AISettingsService

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
    def __init__(
        self,
        api_key: str,
        flow: FlowDTO,
        aisettings_service: AISettingsService,
        model: str = "gpt-4o-mini", 
        max_retries: int = 2, 
        timeout: float = 15.0,
        cache_size_limit: int = 1000
    ):
        self.cache = {}
        self.flow = flow
        self.model = model
        self.max_retries = max_retries
        self.request_timeout = timeout
        self.cache_size_limit = cache_size_limit
        self.aisettings_service = aisettings_service
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=timeout)

    async def _get_or_create_user_prompt(self, text: str, flow: FlowDTO) -> str:
        try:
            aisettings = await self.aisettings_service.get_aisettings_by_flow(flow)
            return aisettings.prompt
            
        except AISettingsNotFoundError:
            default_prompt = await self._build_system_prompt(text, flow)
            try:
                aisettings = await self.aisettings_service.create_aisettings(
                    flow=flow,
                    prompt=default_prompt,
                    style=str(flow.theme)
                )
                return default_prompt

            except UniqueViolation:
                existing_settings = await self.aisettings_service.get_aisettings_by_flow(flow)
                return existing_settings.prompt
                
            except Exception as create_error:
                logging.error(f"Error creating AI settings: {str(create_error)}")
                return default_prompt
                
        except Exception as e:
            logging.error(f"Error getting flow prompt: {str(e)}")
            return await self._build_system_prompt(text, flow)
        
    async def process(self, text: str, user_id: int) -> str:

        if isinstance(text, list):
            text = " ".join([str(item) for item in text if item])
            
        if not text.strip():
            return ""
        
        cache_key = hash(f"{text}_{self.flow.id}_{user_id}")
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            system_prompt = await self._get_prompt(text, self.flow)
            result = await self._call_ai_with_retry(text, system_prompt)
            
            if len(self.cache) >= self.cache_size_limit:
                self.cache.pop(next(iter(self.cache)))
            
            self.cache[cache_key] = result
            return result
        except Exception as e:
            logging.error(f"Final processing error: {str(e)}")
            return text

    async def _call_ai_with_retry(self, text: str, system_prompt: str) -> str:
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.5,
                    top_p=0.9,
                    max_tokens=2000,
                    timeout=self.request_timeout
                )
                result = response.choices[0].message.content.strip()
                logging.debug(f"AI request took {time.time() - start_time:.2f}s")
                return result
            except Exception as e:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(1 * (attempt + 1))


    async def _get_prompt(self, text: str, flow: FlowDTO) -> str:
        return await self._get_or_create_user_prompt(text, flow)


    async def _build_system_prompt(self, text: str, flow: FlowDTO) -> str:
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
            rules.append(f"5. Use relevant {emoji_type} emojis")
        
        if self.flow.title_highlight:
            rules.append("6. Format title with <b> tags")
        
        if self.flow.cta:
            rules.append(f"7. Add CTA: {self.flow.cta}")
        
        rules.append("Return only the edited content without commentary.")
        return "\n".join(rules)

    def _get_length_instruction(self) -> str:
        length_mapping = {
            "short": "50-100 words",
            "medium": "150-300 words", 
            "long": "500-1000 words"
        }
        return length_mapping.get(self.flow.content_length, "150-300 words")