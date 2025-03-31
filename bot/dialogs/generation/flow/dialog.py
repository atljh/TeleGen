import logging
from datetime import datetime
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram.enums import ParseMode
from aiogram_dialog import DialogManager

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

async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}
    
    selected_channel = (
        start_data.get("selected_channel") 
        or dialog_data.get("selected_channel")
    )
    
    if not selected_channel:
        return {
            "channel_name": "Канал не вибрано",
            "channel_id": "N/A",
            "created_at": datetime.now()
        }
    
    dialog_manager.dialog_data["selected_channel"] = selected_channel
    
    return {
        "channel_name": selected_channel.name,
        "channel_id": selected_channel.channel_id,
        "created_at": selected_channel.created_at,
    }

def flow_dialog():
    return Dialog(
        Window(
            Format("{channel_name}"),
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
            getter=selected_channel_getter
        ),
    )