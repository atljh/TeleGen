from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button

from bot.dialogs.generation.states import GenerationMenu
from dialogs.buffer.states import BufferMenu
from dialogs.settings.states import SettingsMenu
from dialogs.support.states import SupportMenu

async def on_generation_click(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    await callback.answer()
    await manager.start(GenerationMenu.main, mode=StartMode.RESET_STACK)

async def on_buffer_click(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    await callback.answer()
    await manager.start(BufferMenu.preview, mode=StartMode.RESET_STACK)

async def on_settings_click(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    await callback.answer()
    await manager.start(SettingsMenu.main, mode=StartMode.RESET_STACK)

async def on_support_click(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    await callback.answer()
    await manager.start(SupportMenu.main, mode=StartMode.RESET_STACK)
