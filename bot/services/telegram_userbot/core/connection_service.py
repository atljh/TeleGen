import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from telethon import TelegramClient

from ..types import ConnectionError, TelegramEntity

# from telethon.errors import ConnectionError as TelethonConnectionError


class ConnectionService:
    def __init__(
        self,
        session_path: str,
        api_id: int,
        api_hash: str,
        connection_retries: int = 5,
        auto_reconnect: bool = True,
    ):
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.connection_retries = connection_retries
        self.auto_reconnect = auto_reconnect
        self.logger = logging.getLogger(__name__)

    def create_client(self) -> TelegramClient:
        return TelegramClient(
            session=self.session_path,
            api_id=self.api_id,
            api_hash=self.api_hash,
            connection_retries=self.connection_retries,
            auto_reconnect=self.auto_reconnect,
            use_ipv6=False,
            proxy=None,
        )

    async def connect_client(self, client: TelegramClient) -> bool:
        try:
            await client.connect()
            return True
        # except TelethonConnectionError as e:
        #     self.logger.error(f"Connection failed: {str(e)}")
        #     raise ConnectionError(f"Connection failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected connection error: {str(e)}")
            raise ConnectionError(f"Unexpected error: {str(e)}")

    async def disconnect_client(self, client: TelegramClient) -> bool:
        try:
            await client.disconnect()
            return True
        except Exception as e:
            self.logger.warning(f"Error during client disconnect: {str(e)}")
            return False

    async def reconnect_client(self, client: TelegramClient) -> bool:
        try:
            await self.disconnect_client(client)
            await asyncio.sleep(1)
            return await self.connect_client(client)
        except Exception as e:
            self.logger.error(f"Reconnection failed: {str(e)}")
            return False

    def is_client_connected(self, client: TelegramClient) -> bool:
        return client.is_connected()

    async def test_connection(self, client: TelegramClient) -> bool:
        try:
            return await client.is_user_authorized()
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
