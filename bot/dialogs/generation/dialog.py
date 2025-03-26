import logging
from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import DialogManager

from bot.containers import Container
from .states import GenerationMenu, ChannelMenu
from .callbacks import (
    on_channel_selected,
    add_channel,
    go_back_to_main
)

async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {
        "channels": channels or []
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
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_main),
            ),
            state=GenerationMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=get_user_channels_data,
        ),
        Window(
            Const("Channel"),
            Column(
                Button(Const("Flow\nСтворити флоу"), id="create_flow", on_click=on_create_flow),
                Button(Const("Буфер"), id="buffer", on_click=on_buffer),
                Button(Const("Забронювати рекалиний топ"), id="book_recall", on_click=on_book_recall),
                Button(Const("Message"), id="message", on_click=on_message),
            ),
            Row(
                Back(Const("<<<Назад")),
            ),
            state=ChannelMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    )