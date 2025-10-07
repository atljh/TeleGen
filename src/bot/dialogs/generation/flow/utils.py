import logging
import os
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo, Message
from aiogram_dialog import DialogManager
from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=100)
def get_media_path(media_url: str) -> str | None:
    if not media_url:
        return None
    if media_url.startswith("http://") or media_url.startswith("https://"):
        return media_url
    return os.path.join(settings.MEDIA_ROOT, media_url.split("/media/")[-1])


async def safe_delete_messages(bot, chat_id: int, message_ids: Sequence[int]) -> None:
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            logger.debug(
                "Failed to delete message %s in chat %s", msg_id, chat_id, exc_info=True
            )


async def send_media_album(
    dialog_manager: DialogManager, post_data: dict[str, Any]
) -> Message | None:
    bot = dialog_manager.middleware_data["bot"]
    chat_id = dialog_manager.middleware_data["event_chat"].id
    message = dialog_manager.event.message

    message_ids = dialog_manager.dialog_data.get("message_ids", [])
    if message_ids:
        await safe_delete_messages(bot, chat_id, message_ids)
        dialog_manager.dialog_data["message_ids"] = []

    try:
        images = post_data.get("images", [])
        videos = post_data.get("videos", [])

        media_items = (images + videos)[:10]
        if not media_items:
            return None

        media_group = []
        for i, item in enumerate(media_items):
            file_url = getattr(item, "url", None)
            if not file_url:
                continue

            media_path = get_media_path(file_url)
            if media_path.startswith("http"):
                file_input = media_path
            else:
                if not os.path.exists(media_path):
                    logger.warning("Media file not found on disk: %s", media_path)
                    continue
                file_input = FSInputFile(media_path)

            caption = post_data.get("content") if i == 0 else None

            if item in images:
                media = InputMediaPhoto(
                    media=file_input,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )
            else:
                media = InputMediaVideo(
                    media=file_input,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )

            media_group.append(media)

        if not media_group:
            return None

        try:
            await message.delete()
        except Exception:
            logger.debug(
                "Failed to delete trigger message before sending media group",
                exc_info=True,
            )

        new_messages = await bot.send_media_group(chat_id=chat_id, media=media_group)
        dialog_manager.dialog_data["message_ids"] = [m.message_id for m in new_messages]

    except Exception as e:
        logger.error("Error sending media album: %s", e, exc_info=True)
        try:
            await dialog_manager.event.answer("⚠️ Не вдалось вiдправити альбом")
        except Exception:
            logger.debug("Failed to notify user about media error", exc_info=True)

    return None
