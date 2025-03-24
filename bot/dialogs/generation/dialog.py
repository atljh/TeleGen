from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back
from aiogram_dialog.widgets.text import Const

from .states import GenerationMenu
from .callbacks import (
    on_channel1,
    on_channel2,
    add_channel,
    go_back_to_main
)

def create_generation_dialog():
    return Dialog(
        Window(
            Const("Оберiть канал\nабо додайте новий"),
            Row(
                Button(Const("Канал1"), id="channel1", on_click=on_channel1),
                Button(Const("Канал2"), id="channel2", on_click=on_channel2),
            ),
            Row(
                Button(Const("Додати канал"), id="add_channel", on_click=add_channel),
            ),
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_main),
            ),
            state=GenerationMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    )