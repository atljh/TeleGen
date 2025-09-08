import logging
from typing import Optional

from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest

from ..types import TelegramEntity


class EntityService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def get_entity(
        self, client: TelegramClient, source_link: str
    ) -> Optional[TelegramEntity]:
        try:
            return await client.get_entity(source_link)
        except Exception as e:
            if "t.me/+" in source_link:
                return await self._join_private_chat(client, source_link)
            else:
                self.logger.error(f"Failed to get entity for {source_link}: {e}")
                return None

    async def _join_private_chat(
        self, client: TelegramClient, source_link: str
    ) -> Optional[TelegramEntity]:
        try:
            invite_hash = self._extract_invite_hash(source_link)
            await client(ImportChatInviteRequest(invite_hash))
            return await client.get_entity(source_link)
        except Exception as join_err:
            self.logger.error(f"Failed to join private chat {source_link}: {join_err}")
            return None

    def _extract_invite_hash(self, source_link: str) -> str:
        return source_link.split("+")[-1]

    async def get_entity_info(
        self, client: TelegramClient, entity: TelegramEntity
    ) -> dict:
        try:
            return {
                "id": entity.id,
                "title": getattr(entity, "title", None),
                "username": getattr(entity, "username", None),
                "participants_count": getattr(entity, "participants_count", None),
                "type": type(entity).__name__,
            }
        except Exception as e:
            self.logger.error(f"Failed to get entity info: {str(e)}")
            return {}

    async def search_entities(
        self, client: TelegramClient, query: str, limit: int = 10
    ) -> list[TelegramEntity]:
        try:
            return await client.get_entity(query)
        except Exception as e:
            self.logger.error(f"Entity search failed: {str(e)}")
            return []

    async def verify_entity_access(
        self, client: TelegramClient, entity: TelegramEntity
    ) -> bool:
        try:
            await client.get_entity(entity)
            return True
        except Exception as e:
            self.logger.warning(f"Entity access verification failed: {str(e)}")
            return False
