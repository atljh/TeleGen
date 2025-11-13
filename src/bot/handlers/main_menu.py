import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, StartMode

from bot.dialogs.buffer.states import BufferMenu
from bot.dialogs.generation.states import GenerationMenu
from bot.dialogs.settings.states import SettingsMenu
from bot.dialogs.support.states import SupportMenu

router = Router()
logger = logging.getLogger(__name__)


async def cleanup_dialog_messages(
    message: types.Message, dialog_manager: DialogManager, state: FSMContext
):
    from bot.utils.message_tracker import clear_message_ids, get_message_ids

    try:
        user_id = message.from_user.id

        message_ids = get_message_ids(user_id)

        try:
            state_data = await state.get_data()
            fsm_message_ids = state_data.get("message_ids", [])
            if fsm_message_ids:
                logger.info(
                    f"Found {len(fsm_message_ids)} message_ids in FSMContext: {fsm_message_ids}"
                )
                message_ids.extend(fsm_message_ids)
        except Exception as e:
            logger.debug(f"Could not access FSMContext: {e}")

        try:
            if dialog_manager and dialog_manager.dialog_data:
                dialog_message_ids = dialog_manager.dialog_data.get("message_ids", [])
                if dialog_message_ids:
                    logger.info(
                        f"Found {len(dialog_message_ids)} message_ids in dialog_data: {dialog_message_ids}"
                    )
                    message_ids.extend(dialog_message_ids)
        except Exception as e:
            logger.debug(f"Could not access dialog_data: {e}")

        message_ids = list(set(message_ids))

        # Also try to delete the message right before the user's message (likely bot's last message)
        if message.message_id > 1:
            prev_message_id = message.message_id - 1
            message_ids.append(prev_message_id)
            logger.info(f"Adding previous message ID: {prev_message_id}")

        # Remove duplicates again
        message_ids = list(set(message_ids))

        if message_ids:
            logger.info(f"Cleaning up {len(message_ids)} messages: {message_ids}")
            bot = message.bot
            deleted_count = 0
            for msg_id in message_ids:
                try:
                    await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
                    deleted_count += 1
                    logger.info(f"✅ Deleted message {msg_id}")
                except Exception as e:
                    logger.warning(f"❌ Could not delete message {msg_id}: {e}")

            logger.info(f"Successfully deleted {deleted_count}/{len(message_ids)} messages")

            clear_message_ids(user_id)
            try:
                await state.update_data(message_ids=[])
            except Exception:
                pass
        else:
            logger.info("No messages to clean up")
    except Exception as e:
        logger.error(f"Error cleaning up messages: {e}", exc_info=True)


@router.message(F.text == "⚙️ Налаштування")
async def handle_settings(
    message: types.Message, dialog_manager: DialogManager, state: FSMContext
):
    await cleanup_dialog_messages(message, dialog_manager, state)
    await dialog_manager.start(state=SettingsMenu.main, mode=StartMode.RESET_STACK)


@router.message(F.text == "✨ Генерацiя")
async def handle_generation(
    message: types.Message, dialog_manager: DialogManager, state: FSMContext
):
    await cleanup_dialog_messages(message, dialog_manager, state)
    await dialog_manager.start(state=GenerationMenu.main, mode=StartMode.RESET_STACK)


@router.message(F.text == "📂 Буфер")
async def handle_buffer(
    message: types.Message, dialog_manager: DialogManager, state: FSMContext
):
    await cleanup_dialog_messages(message, dialog_manager, state)
    await dialog_manager.start(state=BufferMenu.main, mode=StartMode.RESET_STACK)


@router.message(F.text == "❓ Допомога")
async def handle_support(
    message: types.Message, dialog_manager: DialogManager, state: FSMContext
):
    await cleanup_dialog_messages(message, dialog_manager, state)
    await dialog_manager.start(state=SupportMenu.main, mode=StartMode.RESET_STACK)
