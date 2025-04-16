import asyncio
import logging
from telethon import TelegramClient
from bot.database.dtos import FlowDTO

class UserbotService:
    def __init__(self, api_id: int, api_hash: str, phone: str = None, bot_token: str = None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.bot_token = bot_token
        self.client = None
        
    async def initialize(self):
        session_name = 'userbot_session'
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        
        try:
            if not await self.client.is_user_authorized():
                if self.bot_token:
                    await self.client.start(bot_token=self.bot_token)
                elif self.phone:
                    await self.client.start(phone=self.phone)
                else:
                    raise ValueError("Either phone or bot_token must be provided")
        except Exception as e:
            logging.error(f"Telegram auth error: {e}")
            raise

    async def generate_content(self, flow: FlowDTO) -> str:
        if not self.client:
            await self.initialize()
            
        try:
            sources_content = []
            for source in flow.sources:
                if source['type'] == 'telegram':
                    entity = await self.client.get_entity(source['link'])
                    messages = await self.client.get_messages(entity, limit=10)
                    sources_content.extend([msg.text for msg in messages if msg.text])
            
            return self._format_post(sources_content, flow)
        except Exception as e:
            logging.error(f"Error generating content: {e}")
            return "Не удалось сгенерировать контент"
    
    async def get_raw_content(self, sources: list[dict]) -> list[str]:
        content = []
        for source in sources:
            if source['type'] == 'telegram':
                content.extend(await self._get_telegram_content(source['link']))
        return content
    
    async def get_content_from_sources(self, sources: list[dict]) -> list[str]:
        if not sources:
            return []
            
        content = []
        for source in sources:
            try:
                if source['type'] == 'telegram':
                    messages = await self._get_telegram_messages(source['link'])
                    content.extend(msg.text for msg in messages if msg.text)
            except Exception as e:
                logging.error(f"Error processing source {source.get('link')}: {str(e)}")
                continue
                
        return content or ["Нет доступного контента"]
    
    async def _get_telegram_messages(self, source_link: str, limit: int = 10) -> list[str]:
        if not self.client:
            await self.initialize()

        try:
            # Извлекаем username из ссылки (https://t.me/odessa_infonews -> odessa_infonews)
            username = source_link.split('/')[-1]
            
            entity = await self.client.get_entity(username)
            
            messages = await self.client.get_messages(
                entity,
                limit=limit,
                wait_time=2
            )
            
            return [msg.text for msg in messages if hasattr(msg, 'text') and msg.text]
            
        except ValueError as e:
            logging.error(f"Invalid source link {source_link}: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error fetching messages from {source_link}: {str(e)}")
            return []