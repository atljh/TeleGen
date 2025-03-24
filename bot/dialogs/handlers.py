from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager

from aiogram_dialog import DialogManager, StartMode
from dialogs.generation_dialog import GenerationMenu

async def on_generation_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Генерація обрана!")
    await manager.start(state=GenerationMenu.main, mode=StartMode.RESET_STACK)

async def on_buffer_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Буфер обраний!")

async def on_settings_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Налаштування обрані!")

async def on_help_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Допомога обрана!")