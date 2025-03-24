from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button

from dialogs.generation.states import GenerationMenu
from dialogs.buffer.states import BufferMenu

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
    await manager.start(BufferMenu.main, mode=StartMode.RESET_STACK)
