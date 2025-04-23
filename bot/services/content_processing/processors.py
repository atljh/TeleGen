from abc import ABC, abstractmethod
from datetime import datetime
import logging
import re
from typing import Dict, List

import openai


class ContentProcessor(ABC):
    @abstractmethod
    async def process_text(self, content: str) -> str: ...

class TextCleaner(ContentProcessor): ...


class DefaultContentProcessor(ContentProcessor):
    def __init__(self):
        self.link_regex = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.special_chars_regex = re.compile(r'[\u200B-\u200D\uFEFF]')

    async def process_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = self.special_chars_regex.sub('', text)
        text = ' '.join(text.split())
        
        text = self.link_regex.sub('', text)
        
        return text.strip()

class ChatGPTContentProcessor(ContentProcessor):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def process_text(self, text: str) -> str:
        if not text:
            return ""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that processes social media posts. Clean up the text, remove unnecessary links and special characters, and improve readability while preserving the original meaning."},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"ChatGPT processing error: {str(e)}")
            return text
        
# class PostProcessingPipeline:
#     def __init__(self, processors: List[ContentProcessor]):
#         self.processors = processors

#     async def process_post(self, raw_post: Dict) -> ProcessedPost:
#         text = raw_post.get('text', '')
        
#         for processor in self.processors:
#             text = await processor.process_text(text)
        
#         return ProcessedPost(
#             text=text,
#             media=raw_post.get('media', []),
#             is_album=raw_post.get('is_album', False),
#             source=raw_post.get('source', {}),
#             metadata={
#                 'original_text': raw_post.get('text', ''),
#                 'processed_at': datetime.now().isoformat()
#             }
#         )
