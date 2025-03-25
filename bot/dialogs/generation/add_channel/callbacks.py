from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

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

async def process_channel_id(callback: CallbackQuery, button: Button, manager: DialogManager):
    channel_id = "отриманий_ідентифікатор"  
    await manager.update({
        "channel_id": channel_id,
        "channel_name": f"Канал ({channel_id})"
    })
    await manager.switch_to(AddChannelMenu.instructions)