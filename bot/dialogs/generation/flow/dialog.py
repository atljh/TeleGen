
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram.enums import ParseMode

from utils.buttons import (
    go_back_to_channel,
    go_back_to_main
)
from .states import FlowMenu
from .callbacks import (
    on_publish_now,
    on_schedule,
    on_edit,
    on_save_to_buffer
)


def create_flow_dialog():
    return Dialog(
        Window(
            Const("This component is used as the top message in a series.\n\n"
                 "You can scale it, input smiles or supported markdown formatting.\n\n"
                 "15:20"),
            Column(
                Button(Const("Опубликовать сейчас"), id="publish_now", on_click=on_publish_now),
                Button(Const("Запланировать публикацию"), id="schedule", on_click=on_schedule),
                Button(Const("Редактировать"), id="edit", on_click=on_edit),
                Button(Const("Сохранить в буфер"), id="save_to_buffer", on_click=on_save_to_buffer),
            ),
            Row(
                Button(Const("🔙 Назад"), id="go_back_to_channel", on_click=go_back_to_channel),
            ),
            Row(
                Button(Const("Головне меню "), id="go_back_to_main", on_click=go_back_to_main),
            ),
            state=FlowMenu.main,
            parse_mode=ParseMode.HTML,
        ),
    )