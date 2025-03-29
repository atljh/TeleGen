# handlers/events.py
import logging
from aiogram import Router
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, ADMINISTRATOR
from aiogram_dialog import DialogManager
from bot.containers import Container

router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> ADMINISTRATOR))
async def bot_added_as_admin(event: ChatMemberUpdated, dialog_manager: DialogManager):
    logging.info(f"Chat member update received: {event}")
    if event.new_chat_member.user.id == event.bot.id:
        channel_service = Container.channel_service()
        
        await channel_service.get_or_create_channel(
            user_telegram_id=event.from_user.id,
            channel_id=str(event.chat.id),
            name=event.chat.title
        )
        
        await event.answer(
            text=f"✅ Бота добавлено в {event.chat.type} \"{event.chat.title}\" як адміністратора!"
        )

def register_event_handlers(dp: Dispatcher):
    dp.include_router(router)