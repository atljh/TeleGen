from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row, Back
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu 


async def publish_now(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("✅ Публікацію успішно опубліковано!")

async def schedule_publish(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("📅 Публікацію заплановано!")

async def edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("✏️ Відкрито редактор публікації!")

async def delete_draft(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("🗑 Чернетку видалено!")

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
