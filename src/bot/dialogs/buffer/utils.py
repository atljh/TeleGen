import logging
import os
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputMediaPhoto, Message
from aiogram_dialog import DialogManager
from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=100)
def get_media_path(media_url: str) -> str:
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
) -> Message:
    from aiogram.fsm.context import FSMContext

    logger.info("🎬 send_media_album called (buffer)")

    bot = dialog_manager.middleware_data["bot"]
    chat_id = dialog_manager.middleware_data["event_chat"].id
    message = dialog_manager.event.message
    user_id = dialog_manager.event.from_user.id

    logger.info(f"User ID: {user_id}, Chat ID: {chat_id}")

    message_ids = dialog_manager.dialog_data.get("message_ids", [])
    if message_ids:
        await safe_delete_messages(bot, chat_id, message_ids)
        dialog_manager.dialog_data["message_ids"] = []

    # Get FSMContext
    state: FSMContext = dialog_manager.middleware_data.get("state")

    try:
        images = post_data.get("images", [])[:10]
        if not images:
            return None

        media_group: list[InputMediaPhoto] = []
        for i, image in enumerate(images):
            image_url = getattr(image, "url", None)
            if not image_url:
                continue

            media_path = get_media_path(image_url)
            if not os.path.exists(media_path):
                logger.warning("Media file not found on disk: %s", media_path)
                continue

            caption = post_data.get("content") if i == 0 else None
            media = InputMediaPhoto(
                media=FSInputFile(media_path),
                # caption=caption,
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
        message_ids = [m.message_id for m in new_messages]
        logger.info(f"📤 Sent media group, got {len(message_ids)} message IDs: {message_ids}")

        dialog_manager.dialog_data["message_ids"] = message_ids
        logger.info(f"💾 Saved to dialog_data")

        # Save to global message tracker
        from bot.utils.message_tracker import save_message_ids

        logger.info(f"📍 About to save to global tracker for user {user_id}")
        save_message_ids(user_id, message_ids)
        logger.info(f"✅ Saved to global tracker")

        # Also try to save to FSMContext as backup
        if state:
            try:
                await state.update_data(message_ids=message_ids)
                logger.info(f"💾 Saved to FSMContext")
            except Exception as e:
                logger.debug(f"Could not save message_ids to FSMContext: {e}")
        else:
            logger.warning("⚠️ FSMContext is None")

    except Exception as e:
        logger.error("Error sending media album: %s", e, exc_info=True)
        try:
            await dialog_manager.event.answer("⚠️ Не вдалось вiдправити альбом")
        except Exception:
            logger.debug("Failed to notify user about media error", exc_info=True)

    return None
