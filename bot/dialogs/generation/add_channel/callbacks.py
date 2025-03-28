from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from .states import AddChannelMenu
from dialogs.generation.states import GenerationMenu
from bot.utils.permissions import check_bot_permissions
from bot.utils.validation import is_valid_channel
from bot.containers import Container

import logging

from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter

channel_router = Router()


@channel_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=True))
async def handle_chat_member_update(event: ChatMemberUpdated, dialog_manager: DialogManager):
    logging.info(event)
    if event.new_chat_member.user.id == event.bot.id:
        if event.new_chat_member.status in ['administrator', 'creator']:
            channel_service = Container.channel_service()
            await channel_service.get_or_create_channel(
                user_telegram_id=event.from_user.id,
                channel_id=str(event.chat.id),
                name=event.chat.title
            )
            
            await dialog_manager.start(
                AddChannelMenu.success,
                data={
                    "channel_name": event.chat.title,
                    "channel_id": str(event.chat.id)
                }
            )

async def check_permissions(callback: CallbackQuery, button: Button, manager: DialogManager):
    bot = manager.middleware_data["bot"]
    channel_id = manager.dialog_data.get("channel_id")
    
    if not channel_id:
        await callback.answer("❌ Будь ласка, спочатку вкажіть канал")
        return
    
    try:
        chat = await bot.get_chat(channel_id)
        permissions = await bot.get_chat_member(chat.id, bot.id)
        
        if not all([
            permissions.can_post_messages,
            permissions.can_edit_messages,
            permissions.can_manage_chat
        ]):
            raise PermissionError("Бот не має всіх необхідних прав")
            
        await save_channel_and_proceed(callback.from_user.id, chat, manager)
        
    except Exception as e:
        await handle_permission_error(e, manager)

async def save_channel_and_proceed(telegram_id: int, chat, manager: DialogManager):
    channel_service = Container.channel_service()
    
    channel_dto, created = await channel_service.get_or_create_channel(
        user_telegram_id=telegram_id,
        channel_id=str(chat.id),
        name=chat.title,
        description=getattr(chat, 'description', None)
    )
    
    logging.info(f"Канал {'створено' if created else 'знайдено'}: {channel_dto}")

    if not created:
        await manager.switch_to(GenerationMenu.main)
        return
    
    await manager.update({
        "result": f"✅ Канал {chat.title} успішно додано!",
        "channel_name": chat.title,
        "channel_id": str(chat.id),
        "is_new_channel": created
    })
    
    await manager.switch_to(AddChannelMenu.success)

async def handle_permission_error(error, manager):
    error_msg = str(error)
    if "Not enough rights" in error_msg:
        error_msg = "❌ Бот не має всіх необхідних прав!"
    
    await manager.update({"result": error_msg})
    await manager.switch_to(AddChannelMenu.check_permissions)

async def on_success_channel_add(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    channel_name = manager.dialog_data.get("channel_name", "ваш канал")
    await manager.update({"channel_name": channel_name})
    await manager.switch_to(AddChannelMenu.success)


async def process_channel_input(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager
):
    channel_id = message.text.strip()
    
    if not channel_id:
        await message.answer("❌ Будь ласка, введіть ідентифікатор каналу")
        return
    
    if not (channel_id.startswith('@') or channel_id.lstrip('-').isdigit()):
        await message.answer("❌ Невірний формат. Введіть @username або ID каналу")
        return
    
    await manager.update({
        "channel_id": channel_id,
        "channel_name": channel_id if channel_id.startswith('@') else f"ID: {channel_id}"
    })
    
    await manager.switch_to(AddChannelMenu.instructions)

async def create_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Функція в розробці")

async def subscribe(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Функція в розробці")