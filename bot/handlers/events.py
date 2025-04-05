import logging
from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import (
    ChatMemberUpdatedFilter, IS_NOT_MEMBER,
    ADMINISTRATOR, IS_MEMBER,
    KICKED
)
from aiogram_dialog import DialogManager, StartMode
from bot.containers import Container

from bot.database.exceptions import ChannelNotFoundError
from bot.dialogs.generation.add_channel.states import AddChannelMenu

channel_router = Router()

@channel_router.my_chat_member(
    ChatMemberUpdatedFilter(IS_NOT_MEMBER >> ADMINISTRATOR)
)
async def bot_added_as_admin(event: ChatMemberUpdated, dialog_manager: DialogManager):
    if event.new_chat_member.user.id == event.bot.id:
        channel_service = Container.channel_service()

        channel = await channel_service.get_or_create_channel(
            user_telegram_id=event.from_user.id,
            channel_id=str(event.chat.id),
            name=event.chat.title
        )

        me = await event.bot.get_me()

        user_dm = dialog_manager.bg(user_id=event.from_user.id, chat_id=event.from_user.id)

        await user_dm.start(
            AddChannelMenu.success,
            data={
                "channel_id": str(event.chat.id),
                "channel_name": event.chat.title,
                "channel_username": event.chat.username or "",
                "bot_url": f"https://t.me/{me.username}",
                "bot_username": me.username
            },
            mode=StartMode.RESET_STACK
        )

@channel_router.my_chat_member(
    ChatMemberUpdatedFilter(IS_MEMBER >> KICKED)
)
async def bot_removed_from_channel(event: ChatMemberUpdated, dialog_manager: DialogManager):
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
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не вдалося надіслати сповіщення: {e}")
