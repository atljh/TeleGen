from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager

from .states import AddChannelMenu

async def check_permissions(callback: CallbackQuery, button: Button, manager: DialogManager):
    has_permissions = True
    
    await manager.update({
        "result": "✅ Бот має всі необхідні права!" if has_permissions 
                 else "❌ Бот не має необхідних прав!"
    })
    await manager.switch_to(AddChannelMenu.check_permissions)