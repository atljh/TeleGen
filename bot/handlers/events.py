from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import (
    ChatMemberUpdatedFilter, IS_NOT_MEMBER,
    ADMINISTRATOR, IS_MEMBER,
    KICKED
)
from aiogram.enums import ChatMemberStatus
from aiogram_dialog import DialogManager
from bot.containers import Container
import logging

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
        
        try:
            await event.bot.send_message(
                chat_id=event.from_user.id,
                text=f"✅ Бота додано до каналу <b>{event.chat.title}</b> як адміністратора!\n\n"
                     "Тепер ви можете керувати публікаціями через меню бота.",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не вдалося надіслати сповіщення: {e}")


@channel_router.my_chat_member(
    ChatMemberUpdatedFilter(IS_MEMBER >> KICKED)
)
async def bot_removed_from_channel(event: ChatMemberUpdated, dialog_manager: DialogManager):
    if event.new_chat_member.user.id == event.bot.id:
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

def register_event_handlers(dp: Dispatcher):
    dp.include_router(channel_router)