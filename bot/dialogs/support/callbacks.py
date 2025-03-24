from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu


async def instructions(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Інструкції")

async def sms_support(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Зв'язок із підтримкою")


async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
