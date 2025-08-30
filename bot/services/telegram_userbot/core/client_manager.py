import os
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from telethon import TelegramClient

from .connection_service import ConnectionService
from .authorization_service import AuthorizationService
from .entity_service import EntityService
from .download_service import DownloadService
from ..types import TelegramEntity

class TelegramClientManager:
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: Optional[str] = None,
        session_path: Optional[str] = None,
        connection_retries: int = 5,
        auto_reconnect: bool = True,
        download_retries: int = 3
    ):
        self.connection_service = ConnectionService(
            session_path=session_path or os.getenv("SESSION_PATH", "userbot.session"),
            api_id=api_id,
            api_hash=api_hash,
            connection_retries=connection_retries,
            auto_reconnect=auto_reconnect
        )
        
        self.authorization_service = AuthorizationService(phone=phone)
        self.entity_service = EntityService()
        self.download_service = DownloadService(max_retries=download_retries)
        
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[TelegramClient, None]:
        client = self.connection_service.create_client()
        
        try:
            await self.connection_service.connect_client(client)
            
            if not await self.authorization_service.is_authorized(client):
                await self.authorization_service.authorize_client(client)
            
            yield client
            
        except Exception as e:
            self.logger.error(f"Помилка Telegram клієнта: {str(e)}")
            raise
        finally:
            await self.connection_service.disconnect_client(client)

    async def get_entity(self, client: TelegramClient, source_link: str) -> Optional[TelegramEntity]:
        return await self.entity_service.get_entity(client, source_link)

    async def download_media_with_retry(
        self,
        client: TelegramClient,
        media,
        file_path: str,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None
    ) -> bool:
        return await self.download_service.download_media_with_retry(
            client, media, file_path, max_retries, retry_delay
        )

    async def get_messages_batch(
        self,
        client: TelegramClient,
        entity: TelegramEntity,
        limit: int,
        offset_id: int = 0
    ) -> list:
        try:
            return await client.get_messages(entity, limit=limit, offset_id=offset_id)
        except Exception as e:
            self.logger.error(f"Failed to get messages: {str(e)}")
            return []

    def is_client_connected(self, client: TelegramClient) -> bool:
        return self.connection_service.is_client_connected(client)

    async def reconnect_client(self, client: TelegramClient):
        return await self.connection_service.reconnect_client(client)

    async def test_connection(self, client: TelegramClient) -> bool:
        return await self.connection_service.test_connection(client)

    async def get_entity_info(self, client: TelegramClient, entity: TelegramEntity) -> dict:
        return await self.entity_service.get_entity_info(client, entity)

    async def download_media_batch(
        self,
        client: TelegramClient,
        media_items: list,
        output_dir: str,
        max_concurrent: int = 5
    ) -> list:
        return await self.download_service.download_media_batch(
            client, media_items, output_dir, max_concurrent
        )