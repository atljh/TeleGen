from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager

from aiogram_dialog import DialogManager, StartMode

async def on_settings_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Налаштування обрані!")

async def on_help_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Допомога обрана!")