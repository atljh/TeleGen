import logging

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import (
    ADMINISTRATOR,
    IS_MEMBER,
    IS_NOT_MEMBER,
    KICKED,
    ChatMemberUpdatedFilter,
    ExceptionTypeFilter,
)
from aiogram.types import ChatMemberUpdated
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.api.exceptions import UnknownIntent

from bot.containers import Container
from bot.database.exceptions import ChannelLimitExceeded, ChannelNotFoundError
from bot.dialogs.generation.add_channel.states import AddChannelMenu

channel_router = Router()


@channel_router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR),
    F.chat.type == ChatType.CHANNEL,
)
async def on_bot_added_to_channel(
    event: ChatMemberUpdated, dialog_manager: DialogManager
):
    channel_service = Container.channel_service()
    try:
        await channel_service.get_or_create_channel(
            user_telegram_id=event.from_user.id,
            channel_id=str(event.chat.id),
            name=event.chat.title,
        )

        me = await event.bot.get_me()

        user_dm = dialog_manager.bg(
            user_id=event.from_user.id, chat_id=event.from_user.id
        )

        await user_dm.start(
            AddChannelMenu.success,
            data={
                "channel_id": str(event.chat.id),
                "channel_name": event.chat.title,
                "bot_username": me.username,
            },
            mode=StartMode.RESET_STACK,
        )

    except ChannelLimitExceeded as e:
        logging.warning(f"Ліміт користувача: {e}")
        await event.bot.send_message(event.from_user.id, f"{e}")
        try:
            await event.bot.leave_chat(event.chat.id)
        except Exception as leave_error:
            logging.error(f"Не вдалося вийти з каналу {event.chat.id}: {leave_error}")

    except ValueError as e:
        logging.warning(
            f"ValueError при додаванні каналу для {event.from_user.id}: {e}"
        )
        await event.bot.send_message(
            event.from_user.id, f"❌ Не вдалося додати канал: {e}"
        )
        try:
            await event.bot.leave_chat(event.chat.id)
        except Exception as leave_error:
            logging.error(f"Не вдалося вийти з каналу {event.chat.id}: {leave_error}")

    except Exception as e:
        logging.error(
            f"Помилка при додаванні каналу для {event.from_user.id}: {e}", exc_info=True
        )
        await event.bot.send_message(
            event.from_user.id, "❌ Помилка при додаванні каналу. Спробуйте ще раз."
        )
        try:
            await event.bot.leave_chat(event.chat.id)
        except Exception as leave_error:
            logging.error(f"Не вдалося вийти з каналу {event.chat.id}: {leave_error}")


@channel_router.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> KICKED))
async def bot_removed_from_channel(
    event: ChatMemberUpdated, dialog_manager: DialogManager
):
    if event.new_chat_member.user.id == event.bot.id:
        channel_service = Container.channel_service()
        try:
            await channel_service.delete_channel(str(event.chat.id))
        except ChannelNotFoundError:
            pass
        try:
            await event.bot.send_message(
                chat_id=event.from_user.id,
                text=f"❌ Бота було видалено з каналу <b>{event.chat.title}</b>\n\n"
                f"ID каналу: <code>{event.chat.id}</code>\n"
                "Публікації в цей канал більше неможливі.",
                parse_mode="HTML",
            )
        except Exception as e:
            logging.error(f"Не вдалося надіслати сповіщення: {e}")


@channel_router.errors(ExceptionTypeFilter(UnknownIntent))
async def handle_unknown_intent(event):
    if event.update.message:
        await event.update.message.answer("/start.")
    return True


@channel_router.errors()
async def global_error_handler(event):
    logging.error("Unhandled exception occurred", exc_info=event.exception)
    if event.update.message:
        await event.update.message.answer("Cпробуйте пiзнiше.")
    return True
