from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const

from .states import SupportMenu

from .callbacks import (
    instructions,
    sms_support,
    go_back_to_main
)


def create_support_dialog():
    return Dialog(
        Window(
            Const("Допомога"),
            Row(
                Button(Const("Інструкції"), id="instructions", on_click=instructions),
                Button(Const("Зв'язок із підтримкою"), id="sms_support", on_click=sms_support),
            ),
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_main),
            ),
            state=SupportMenu.main,
        )
    )