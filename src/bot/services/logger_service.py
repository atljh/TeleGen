import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import requests
from aiogram import Bot
from django.conf import settings

from bot.database.models.user import UserDTO as BotUser


class LogLevel(Enum):
    INFO = "📋"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    MONEY = "💳"
    SETTINGS = "⚙️"
    GENERATION = "✨"
    CHANNEL = "📢"
    USER = "👤"
    SYSTEM = "🖥️"
    SECURITY = "🔒"


@dataclass
class LogEvent:
    level: LogLevel
    message: str
    user_id: int | None = None
    username: str | None = None
    additional_data: dict | None = None


class TelegramLogger:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.log_channel_id = settings.TELEGRAM_LOG_CHANNEL_ID
        self.enabled = bool(self.log_channel_id)

    def _escape_markdown(self, text: str) -> str:
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return "".join(f"\\{char}" if char in escape_chars else char for char in text)

    def _format_additional_data(self, data: dict) -> str:
        if not data:
            return ""

        lines = []
        for key, value in data.items():
            if value is not None:
                escaped_key = self._escape_markdown(str(key))
                escaped_value = self._escape_markdown(str(value))
                lines.append(f"• *{escaped_key}:* `{escaped_value}`")

        return "\n".join(lines)

    async def _send_log(self, event: LogEvent) -> bool:
        if not self.enabled:
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            escaped_timestamp = self._escape_markdown(timestamp)
            escaped_message = self._escape_markdown(event.message)

            message_parts = [
                f" \\| `{escaped_timestamp}`",
                "",
                f"📝 *Message:* {escaped_message}",
            ]

            if event.user_id or event.username:
                user_parts = []
                if event.user_id:
                    user_parts.append(f"ID: `{event.user_id}`")
                if event.username:
                    escaped_username = self._escape_markdown(f"@{event.username}")
                    user_parts.append(escaped_username)

                message_parts.append(f"👤 *User:* {', '.join(user_parts)}")

            if event.additional_data:
                formatted_data = self._format_additional_data(event.additional_data)
                if formatted_data:
                    message_parts.extend(["", "📊 *Details:*", formatted_data])

            message_parts.append("")

            full_message = "\n".join(message_parts)

            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=full_message,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
            return True

        except Exception as e:
            print(f"Failed to send log to Telegram: {e}")
            return False

    async def log(self, event: LogEvent) -> bool:
        return await self._send_log(event)

    def log_sync(self, event: LogEvent) -> bool:
        try:
            return asyncio.run(self._send_log(event))
        except Exception:
            return False

    def warning(self, message: str, **kwargs):
        """Standard logging interface: warning level"""
        logging.warning(message)

    def info(self, message: str, **kwargs):
        """Standard logging interface: info level"""
        logging.info(message)

    def error(self, message: str, **kwargs):
        """Standard logging interface: error level"""
        logging.error(message)

    def debug(self, message: str, **kwargs):
        """Standard logging interface: debug level"""
        logging.debug(message)

    async def user_created_channel(
        self, user: BotUser, channel_name: str, channel_id: int
    ) -> bool:
        event = LogEvent(
            level=LogLevel.CHANNEL,
            message="User created a new channel",
            user_id=user.id,
            username=user.username,
            additional_data={
                "Channel ID": channel_id,
                "Channel Name": channel_name,
                "Channel Title": channel_name,
            },
        )
        return await self.log(event)

    async def user_deleted_channel(
        self, user: BotUser, channel_name: str, channel_id: int
    ) -> bool:
        event = LogEvent(
            level=LogLevel.CHANNEL,
            message="User deleted channel",
            user_id=user.id,
            username=user.username,
            additional_data={
                "Channel ID": channel_id,
                "Channel Name": channel_name,
                "Channel Title": channel_name,
            },
        )
        return await self.log(event)

    async def user_started_generation(
        self,
        user: BotUser,
        flow_name: str,
        flow_id: int,
        telegram_volume,
        web_volume,
        auto_generate: bool = False,
    ) -> bool:
        event = LogEvent(
            level=LogLevel.GENERATION,
            message="User started content generation",
            user_id=user.id,
            username=user.username,
            additional_data={
                "Generation_type": (
                    "Auto generation" if auto_generate else "Force generation"
                ),
                "Flow ID": flow_id,
                "Flow Name": flow_name,
                "Telegram Volume": telegram_volume,
                "Web Volume": web_volume,
                "Status": "Started",
            },
        )
        return await self.log(event)

    async def generation_completed(
        self,
        user: BotUser,
        flow_name: str,
        flow_id: int,
        result: str,
        auto_generate: bool = False,
    ) -> bool:
        event = LogEvent(
            level=LogLevel.SUCCESS,
            message="Content generation completed successfully",
            user_id=user.id,
            username=user.username,
            additional_data={
                "Generation_type": (
                    "Auto generation" if auto_generate else "Force generation"
                ),
                "Flow ID": flow_id,
                "Flow Name": flow_name,
                "Result": result,
                "Status": "Completed",
            },
        )
        return await self.log(event)

    async def user_registered(self, user: BotUser) -> bool:
        event = LogEvent(
            level=LogLevel.USER,
            message="New user registered in the system",
            user_id=user.id,
            username=user.username,
            additional_data={
                "First Name": user.first_name,
                "Last Name": user.last_name,
                "Registration Date": datetime.now().strftime("%Y-%m-%d"),
            },
        )
        return await self.log(event)

    async def payment_received(
        self, user: BotUser, amount: float, currency: str, plan: str
    ) -> bool:
        event = LogEvent(
            level=LogLevel.MONEY,
            message="Payment received successfully",
            user_id=user.user_id,
            username=user.username,
            additional_data={
                "Amount": f"{amount} {currency}",
                "Plan": plan,
                "Payment Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Status": "Completed",
            },
        )
        return await self.log(event)

    async def settings_updated(
        self,
        user: Any,
        setting_type: str,
        old_value: str,
        new_value: str,
        additional_data: dict | None = None,
    ) -> bool:
        if not self.enabled:
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            escaped_timestamp = self._escape_markdown(timestamp)

            message_parts = [
                f"⚙️ *Settings Updated* \\| `{escaped_timestamp}`",
                "",
                f"*Type:* {self._escape_markdown(setting_type)}",
            ]

            if user:
                user_parts = []
                if hasattr(user, "id"):
                    user_parts.append(f"ID: `{user.id}`")
                if hasattr(user, "username"):
                    escaped_username = self._escape_markdown(f"@{user.username}")
                    user_parts.append(escaped_username)

                if user_parts:
                    message_parts.append(f"*User:* {', '.join(user_parts)}")

            if old_value:
                message_parts.extend(
                    [
                        "",
                        "*Old Values:*",
                        f"```\n{self._escape_markdown(old_value)}\n```",
                    ]
                )

            if new_value:
                message_parts.extend(
                    [
                        "",
                        "*New Values:*",
                        f"```\n{self._escape_markdown(new_value)}\n```",
                    ]
                )

            if additional_data:
                formatted_data = self._format_additional_data(additional_data)
                if formatted_data:
                    message_parts.extend(["", "*Details:*", formatted_data])

            message_parts.append("")

            full_message = "\n".join(message_parts)

            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=full_message,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
            return True

        except Exception as e:
            print(f"Failed to send settings update log: {e}")
            return False

    async def error_occurred(
        self,
        error_message: str,
        user: BotUser | None = None,
        context: dict | None = None,
    ) -> bool:
        event = LogEvent(
            level=LogLevel.ERROR,
            message="An error occurred in the system",
            user_id=user.id if user else None,
            username=user.username if user else None,
            additional_data={
                "Error Message": (
                    error_message[:200] + "..."
                    if len(error_message) > 200
                    else error_message
                ),
                "Error Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **(context or {}),
            },
        )
        return await self.log(event)

    async def system_startup(self) -> bool:
        event = LogEvent(
            level=LogLevel.SYSTEM,
            message="System started successfully",
            additional_data={
                "Startup Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "Status": "Online",
                "Version": "1.0.0",
            },
        )
        return await self.log(event)

    async def security_event(
        self,
        event_type: str,
        user: BotUser | None = None,
        details: dict | None = None,
    ) -> bool:
        event = LogEvent(
            level=LogLevel.SECURITY,
            message=f"Security event: {event_type}",
            user_id=user.user_id if user else None,
            username=user.username if user else None,
            additional_data=details,
        )
        return await self.log(event)


_logger_instance = None


def get_logger() -> TelegramLogger | None:
    return _logger_instance


def init_logger(bot: Bot) -> TelegramLogger:
    global _logger_instance
    _logger_instance = TelegramLogger(bot)
    return _logger_instance


class SyncTelegramLogger:
    def __init__(self, bot_token: str | None = None):
        self.bot_token = bot_token
        self.log_channel_id = settings.TELEGRAM_LOG_CHANNEL_ID
        self.enabled = bool(bot_token)
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def _escape_markdown(self, text: str) -> str:
        if not text:
            return ""
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        for char in escape_chars:
            text = text.replace(char, f"\\{char}")
        return text

    def _format_additional_data(self, data: dict) -> str:
        if not data:
            return ""

        lines = []
        for key, value in data.items():
            if value is not None:
                escaped_key = self._escape_markdown(str(key))
                escaped_value = self._escape_markdown(str(value))
                lines.append(f"• *{escaped_key}:* `{escaped_value}`")

        return "\n".join(lines)

    def _send_log_sync(self, event_data: dict) -> bool:
        if not self.enabled:
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            escaped_timestamp = self._escape_markdown(timestamp)
            escaped_message = self._escape_markdown(event_data.get("message", ""))

            message_parts = [
                f" \\| `{escaped_timestamp}`",
                "",
                f"📝 *Message:* {escaped_message}",
            ]

            if event_data.get("user_id") or event_data.get("username"):
                user_parts = []
                if event_data.get("user_id"):
                    user_parts.append(f"ID: `{event_data['user_id']}`")
                if event_data.get("username"):
                    escaped_username = self._escape_markdown(
                        f"@{event_data['username']}"
                    )
                    user_parts.append(escaped_username)

                message_parts.append(f"👤 *User:* {', '.join(user_parts)}")

            if event_data.get("additional_data"):
                formatted_data = self._format_additional_data(
                    event_data["additional_data"]
                )
                if formatted_data:
                    message_parts.extend(["", "📊 *Details:*", formatted_data])

            message_parts.append("")

            full_message = "\n".join(message_parts)

            payload = {
                "chat_id": self.log_channel_id,
                "text": full_message,
                "parse_mode": "MarkdownV2",
                "disable_web_page_preview": True,
            }

            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()

            return True

        except Exception as e:
            logging.error(f"Failed to send log to Telegram: {e}")
            return False

    def user_started_generation(
        self,
        user,
        flow_name: str,
        flow_id: int,
        telegram_volume: int,
        web_volume: int,
        auto_generate: bool = False,
    ) -> bool:
        event_data = {
            "message": "User started content generation",
            "user_id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
            "additional_data": {
                "Generation_type": (
                    "Auto generation" if auto_generate else "Force generation"
                ),
                "Flow": flow_name,
                "Flow ID": flow_id,
                "Telegram Volume": telegram_volume,
                "Web Volume": web_volume,
            },
        }
        return self._send_log_sync(event_data)

    def generation_completed(
        self,
        user: BotUser,
        flow_name: str,
        flow_id: int,
        result: str,
        auto_generate: bool = False,
    ) -> bool:
        event_data = {
            "message": "Content generation completed",
            "user_id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
            "additional_data": {
                "Generation_type": (
                    "Auto generation" if auto_generate else "Force generation"
                ),
                "Flow": flow_name,
                "Flow ID": flow_id,
                "Result": result,
            },
        }
        return self._send_log_sync(event_data)

    def generation_failed(self, flow_id: int, error_message: str) -> bool:
        event_data = {
            "message": "Content generation failed",
            "additional_data": {"Flow ID": flow_id, "Error": error_message},
        }
        return self._send_log_sync(event_data)

    def warning(self, message: str, **kwargs):
        """Standard logging interface: warning level"""
        logging.warning(message)

    def info(self, message: str, **kwargs):
        """Standard logging interface: info level"""
        logging.info(message)

    def error(self, message: str, **kwargs):
        """Standard logging interface: error level"""
        logging.error(message)

    def debug(self, message: str, **kwargs):
        """Standard logging interface: debug level"""
        logging.debug(message)
