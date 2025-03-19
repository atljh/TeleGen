from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup

class BufferMenu(StatesGroup):
    main = State()

async def publish_now(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("✅ Публікацію успішно опубліковано!")

async def schedule_publish(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("📅 Публікацію заплановано!")

async def edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("✏️ Відкрито редактор публікації!")

async def delete_draft(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("🗑 Чернетку видалено!")

buffer_dialog = Dialog(
    Window(
        Const("📌 <b>Буфер публікацій</b>\n\nОберіть дію:"),
        Row(
            Button(Const("✅ Опублікувати зараз"), id="publish_now", on_click=publish_now),
            Button(Const("📅 Запланувати"), id="schedule_publish", on_click=schedule_publish),
        ),
        Row(
            Button(Const("✏️ Редагувати"), id="edit_post", on_click=edit_post),
            Button(Const("🗑 Видалити чернетку"), id="delete_draft", on_click=delete_draft),
        ),
        Back(Const("🔙 Назад")),
        state=BufferMenu.main,
    )
)
