import logging

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from bot.services.logger_service import LogEvent, LogLevel, get_logger

from ..types import AuthorizationError


class AuthorizationService:
    def __init__(self, phone: str | None = None):
        self.phone = phone
        self.logger = get_logger()

    async def authorize_client(self, client: TelegramClient) -> bool:
        try:
            await client.start(
                phone=self.phone, code_callback=lambda: None, password=lambda: None
            )
            return True

        except SessionPasswordNeededError as e:
            await self._handle_password_needed()
            raise AuthorizationError("Two-factor authentication required") from e

        except EOFError as e:
            await self._handle_eof_error()
            raise AuthorizationError("Reauthorization required") from e

        except Exception as e:
            await self._handle_authorization_error(e)
            raise AuthorizationError(f"Authorization failed: {e!s}") from e

    async def is_authorized(self, client: TelegramClient) -> bool:
        try:
            return await client.is_user_authorized()
        except Exception as e:
            self.logger.error(f"Authorization check failed: {e!s}")
            return False

    async def _handle_password_needed(self):
        logging.error("Two-factor authentication required for Userbot!")
        if self.loggerr:
            await self.logger.log(
                LogEvent(
                    level=LogLevel.SECURITY,
                    message="Two-factor authentication required for Userbot!",
                    additional_data={"Event": "2FA Required"},
                )
            )

    async def _handle_eof_error(self):
        logging.error("Userbot requires reauthorization!")
        if self.loggerr:
            await self.logger.log(
                LogEvent(
                    level=LogLevel.SECURITY,
                    message="Userbot requires reauthorization!",
                    additional_data={"Event": "EOF / Session Expired"},
                )
            )

    async def _handle_authorization_error(self, error: Exception):
        logging.error(f"Authorization error: {error!s}")
        if self.loggerr:
            await self.logger.log(
                LogEvent(
                    level=LogLevel.ERROR,
                    message=f"Authorization error: {error!s}",
                    additional_data={"Event": "Auth Error"},
                )
            )

    async def send_code_request(self, client: TelegramClient) -> str | None:
        try:
            return await client.send_code_request(self.phone)
        except Exception as e:
            self.logger.error(f"Code request failed: {e!s}")
            return None

    async def sign_in_with_code(self, client: TelegramClient, code: str) -> bool:
        try:
            await client.sign_in(phone=self.phone, code=code)
            return True
        except Exception as e:
            self.logger.error(f"Sign in with code failed: {e!s}")
            return False

    async def sign_in_with_password(
        self, client: TelegramClient, password: str
    ) -> bool:
        try:
            await client.sign_in(password=password)
            return True
        except Exception as e:
            self.logger.error(f"Sign in with password failed: {e!s}")
            return False
