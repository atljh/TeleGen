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

async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {
        "channels": channels or []
    }

async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}
    
    selected_channel = (
        start_data.get("selected_channel") 
        or dialog_data.get("selected_channel")
    )
    channel_flow = (
        start_data.get("channel_flow") 
        or dialog_data.get("channel_flow")
    )
    
    if not selected_channel:
        return {
            "channel_name": "Канал не вибрано",
            "channel_id": "N/A",
            "created_at": datetime.now()
        }
    
    dialog_manager.dialog_data["selected_channel"] = selected_channel
    dialog_manager.dialog_data["channel_flow"] = channel_flow

    
    return {
        "channel_name": selected_channel.name,
        "channel_id": selected_channel.channel_id,
        "created_at": selected_channel.created_at,
        "channel_flow": channel_flow.name if channel_flow else ''
    }
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
            Row(
                Button(Const("🔙 Назад"), id="back"),
            ),
            state=GenerationMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=get_user_channels_data,
        ),
        Window(
            Format("📢 <b>Назва: {channel_name}</b>\n<b>Флоу: {channel_flow}</b>\n"),
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