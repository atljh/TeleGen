import asyncio
import logging
from telethon import TelegramClient
from bot.database.dtos import FlowDTO

class UserbotService:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        
    async def generate_content(self, flow: FlowDTO) -> str:
        async with TelegramClient('userbot_session', self.api_id, self.api_hash) as client:
            sources_content = []
            for source in flow.sources:
                if source['type'] == 'telegram':
                    entity = await client.get_entity(source['link'])
                    messages = await client.get_messages(entity, limit=10)
                    sources_content.extend([msg.text for msg in messages if msg.text])
            
            return self._format_post(sources_content, flow)
    
    def _format_post(self, sources: list[str], flow: FlowDTO) -> str:
        """Форматирование поста согласно настройкам флоу"""