from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const

from .states import SettingsMenu

from .callbacks import (
    on_channel1,
    on_channel2,
    pay_subscription,
    go_back_to_main
)

def create_settings_dialog():
    return Dialog(
        Window(
            Const("Налаштування\n\nОберiть канал"),
            Row(
                Button(Const("Канал1"), id="channel1", on_click=on_channel1),
                Button(Const("Канал2"), id="channel2", on_click=on_channel2),
            ),
            Row(
                Button(Const("Оплата пiдписки"), id="pay_subscription", on_click=pay_subscription),
            ),
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_main),
            ),
            state=SettingsMenu.main,
        )
    )