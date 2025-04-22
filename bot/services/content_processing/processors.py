from abc import ABC, abstractmethod
import logging

import openai


class ContentProcessor(ABC):
    @abstractmethod
    async def process(self, content: str) -> str: ...

class TextCleaner(ContentProcessor): ...


class ChatGPTContentProcessor(ContentProcessor):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
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