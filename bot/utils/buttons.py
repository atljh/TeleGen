from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button

from dialogs.main.states import MainMenu 
from dialogs.generation.states import GenerationMenu

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)

async def go_back_to_generation(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(GenerationMenu.main, mode=StartMode.RESET_STACK)

async def go_back_to_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(GenerationMenu.channel_main, mode=StartMode.RESET_STACK)

