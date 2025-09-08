import logging
from typing import Optional

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from bot.utils.notifications import notify_admins

from ..types import AuthorizationError


class AuthorizationService:
    def __init__(self, phone: Optional[str] = None):
        self.phone = phone
        self.logger = logging.getLogger(__name__)

    async def authorize_client(self, client: TelegramClient) -> bool:
        try:
            await client.start(
                phone=self.phone, code_callback=lambda: None, password=lambda: None
            )
            return True

        except SessionPasswordNeededError:
            await self._handle_password_needed()
            raise AuthorizationError("Two-factor authentication required")

        except EOFError:
            await self._handle_eof_error()
            raise AuthorizationError("Reauthorization required")

        except Exception as e:
            await self._handle_authorization_error(e)
            raise AuthorizationError(f"Authorization failed: {str(e)}")

    async def is_authorized(self, client: TelegramClient) -> bool:
        try:
            return await client.is_user_authorized()
        except Exception as e:
            self.logger.error(f"Authorization check failed: {str(e)}")
            return False

    async def _handle_password_needed(self):
        self.logger.error("Two-factor authentication required for Userbot!")
        await notify_admins("🔐 Потрібна двофакторна аутентифікація для Userbot!")

    async def _handle_eof_error(self):
        self.logger.error("Userbot requires reauthorization!")
        await notify_admins("⚠️ Userbot потребує повторної авторизації!")

    async def _handle_authorization_error(self, error: Exception):
        self.logger.error(f"Authorization error: {str(error)}")
        await notify_admins(f"❌ Помилка авторизації Userbot: {str(error)}")

    async def send_code_request(self, client: TelegramClient) -> Optional[str]:
        try:
            return await client.send_code_request(self.phone)
        except Exception as e:
            self.logger.error(f"Code request failed: {str(e)}")
            return None

    async def sign_in_with_code(self, client: TelegramClient, code: str) -> bool:
        try:
            await client.sign_in(phone=self.phone, code=code)
            return True
        except Exception as e:
            self.logger.error(f"Sign in with code failed: {str(e)}")
            return False

    async def sign_in_with_password(
        self, client: TelegramClient, password: str
    ) -> bool:
        try:
            await client.sign_in(password=password)
            return True
        except Exception as e:
            self.logger.error(f"Sign in with password failed: {str(e)}")
            return False
