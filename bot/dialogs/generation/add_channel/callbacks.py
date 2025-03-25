from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from .states import AddChannelMenu
from bot.utils.permissions import check_bot_permissions

async def check_permissions(callback: CallbackQuery, button: Button, manager: DialogManager):
    bot = manager.middleware_data["bot"]
    chat_id = manager.dialog_data.get("channel_id")
    
    if not chat_id:
        await callback.answer("❌ Спочатку вкажіть канал")
        return
    
    permissions = await check_bot_permissions(bot, chat_id)
    
    if permissions:
        result = (
            "✅ Бот має всі необхідні права:\n"
            f"• Надсилання повідомлень: {'Так' if permissions['can_post_messages'] else 'Ні'}\n"
            f"• Редагування повідомлень: {'Так' if permissions['can_edit_messages'] else 'Ні'}\n"
            f"• Видалення повідомлень: {'Так' if permissions['can_delete_messages'] else 'Ні'}"
        )
    else:
        result = "❌ Не вдалося перевірити права. Переконайтесь, що бот доданий до каналу як адміністратор"
    
    await manager.update({"result": result})
    await manager.switch_to(AddChannelMenu.check_permissions)

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