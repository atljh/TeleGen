from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from .states import AddChannelMenu
from bot.utils.permissions import check_bot_permissions
from bot.utils.validation import is_valid_channel


async def check_permissions(callback: CallbackQuery, button: Button, manager: DialogManager):
    bot = manager.middleware_data["bot"]
    channel_id = manager.dialog_data.get("channel_id")
    
    if not channel_id:
        await callback.answer("❌ Спочатку вкажіть канал")
        return
    
    if not await is_valid_channel(bot, channel_id):
        await callback.answer("❌ Канал не знайдено або бот не має доступу")
        return

    permissions = await check_bot_permissions(bot, channel_id)
    
    if permissions:
        can_post_messages = permissions['can_post_messages']
        can_edit_messages = permissions['can_edit_messages']
        can_delete_messages = permissions['can_delete_messages']
        if all([can_post_messages, can_edit_messages, can_delete_messages]):
            await on_success_channel_add(callback, button, manager)
            return
        else:
            result = "❌ Бот не має необхiдних прав у каналi"
    else:
        result = "❌ Не вдалося перевірити права. Переконайтесь, що бот доданий до каналу як адміністратор"
    
    # await manager.update({"result": result})
    # await manager.switch_to(AddChannelMenu.check_permissions)
    await callback.answer(result)


async def on_success_channel_add(callback: CallbackQuery, button: Button, manager: DialogManager):
    channel_name = manager.dialog_data.get("channel_name", "ваш канал")
    await manager.update({"channel_name": channel_name})
    await manager.switch_to(AddChannelMenu.success)

async def process_channel_input(message: Message, message_input: MessageInput, manager: DialogManager):
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