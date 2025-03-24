from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu 

async def on_channel1(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Канал1")

async def on_channel2(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Канал2")

async def add_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Додати канал")

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
