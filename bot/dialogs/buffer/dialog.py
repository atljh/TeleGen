from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const

from .states import BufferMenu
from .callbacks import (
    publish_now,
    schedule_publish,
    edit_post,
    delete_draft,
    go_back_to_main
)

def create_buffer_dialog():
    return Dialog(
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
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_main),
            ),
            state=BufferMenu.main,
            parse_mode=ParseMode.HTML
        )
    )