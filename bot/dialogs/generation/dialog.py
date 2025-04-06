import logging
from datetime import datetime
from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import DialogManager

from bot.containers import Container
from .states import GenerationMenu
from .callbacks import (
    on_channel_selected,
    add_channel,
    on_create_flow,
    on_buffer,
    on_book_recall,
    on_flow
)
from .gettets import (
    get_user_channels_data,
    selected_channel_getter
)

def create_generation_dialog():
    return Dialog(
        Window(
            Const("Оберiть канал\nабо додайте новий"),
            Group(
                Select(
                    text=Format("{item.name}"),
                    item_id_getter=lambda channel: channel.id,
                    items="channels",
                    id="channel_select",
                    on_click=on_channel_selected,
                ),
                width=2,
            ),
            Row(
                Button(Const("Додати канал"), id="add_channel", on_click=add_channel),
            ),
            state=GenerationMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=get_user_channels_data,
        ),
        Window(
            Format(
                "📢 <b>Назва: {dialog_data[selected_channel].name}</b>\n"
                "📅 <b>Дата додавання:</b> {dialog_data[selected_channel].created_at:%d.%m.%Y}\n\n"
                "<b>Флоу: {channel_flow}</b>"
            ),
            Column(
                Button(Const("Флоу"), id="flow", on_click=on_flow),
                Button(Const("Створити флоу"), id="create_flow", on_click=on_create_flow),
                Button(Const("Буфер"), id="buffer", on_click=on_buffer),
                Button(Const("Забронювати рекламний топ"), id="book_recall", on_click=on_book_recall),
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            state=GenerationMenu.channel_main,
            parse_mode=ParseMode.HTML,
            getter=selected_channel_getter
        )
    )