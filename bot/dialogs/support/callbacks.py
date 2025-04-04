from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode


async def instructions(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Інструкції")

async def sms_support(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Зв'язок із підтримкою")

