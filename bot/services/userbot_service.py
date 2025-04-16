import os
import asyncio
import logging
from telethon import TelegramClient
from bot.database.dtos import FlowDTO


class UserbotService:
    def __init__(self, api_id: int, api_hash: str, phone: str = None, session_dir: str = "sessions"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_dir = session_dir
        self.client = None
        self.lock = asyncio.Lock()
        os.makedirs(self.session_dir, exist_ok=True)

    async def initialize(self):
        async with self.lock:
            if self.client and self.client.is_connected():
                return

            session_path = "app/sessions/userbot.session"

            if os.path.exists(session_path):
                logging.info("Session file exists")
            else:
                logging.info("Session file doesnt exists")

            self.client = TelegramClient(
                session=session_path,
                api_id=self.api_id,
                api_hash=self.api_hash,
                connection_retries=5,
                auto_reconnect=True
            )
            
            try:
                await self.client.connect()
                
                if not await self.client.is_user_authorized():
                    logging.info("Starting authorization...")
                    if self.phone:
                        await self.client.start(phone=self.phone)
                    else:
                        raise ValueError("Phone number required")
                        
                logging.info("Telegram client ready")
            except Exception as e:
                logging.error(f"Initialization failed: {str(e)}")
                await self.disconnect()
                raise

    async def disconnect(self):
        async with self.lock:
            if self.client and self.client.is_connected():
                await self.client.disconnect()
            self.client = None

    async def _ensure_client(self):
        if not self.client or not self.client.is_connected():
            await self.initialize()

    async def generate_content(self, flow: FlowDTO) -> str:
        await self._ensure_client()

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

        await self.initialize()
        
        content = []
        for source in sources:
            try:
                if source['type'] == 'telegram':
                    messages = await self._get_telegram_messages(source['link'])
                    content.extend(msg.text for msg in messages if msg.text)
            except Exception as e:
                logging.error(f"Error processing source {source.get('link')}: {str(e)}")
                continue
                
        return content or ["No content available"]

    async def _get_telegram_messages(self, source_link: str) -> list:
        try:
            me = await self.client.get_me()
            entity = await self.client.get_entity(source_link)
            return await self.client.get_messages(entity, limit=10)
        except Exception as e:
            logging.error(f"Error getting messages from {source_link}: {str(e)}")
            return []

    async def get_last_posts(self, sources: list[dict], posts_limit: int = 10) -> list[str]:
        if not sources:
            return []

        await self._ensure_client()
        
        last_posts = []
        for source in sources:
            if source['type'] != 'telegram':
                continue
                
            try:
                entity = await self.client.get_entity(source['link'])
                messages = await self.client.get_messages(
                    entity,
                    limit=posts_limit
                )
                last_posts.extend(msg.text for msg in messages if msg.text)
            except Exception as e:
                logging.error(f"Error processing source {source['link']}: {str(e)}")
                continue
        
        return last_posts