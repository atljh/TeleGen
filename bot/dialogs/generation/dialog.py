import logging
from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import DialogManager

from bot.containers import Container
from .states import GenerationMenu
from .callbacks import (
    on_channel_selected,
    add_channel,
    go_back_to_main
)

async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    # Get dependencies from middleware
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    logging.info(user_telegram_id)
    channels = await channel_service.get_user_channels(user_telegram_id)
    return {
        "channels": channels,
    }

def create_generation_dialog():
    return Dialog(
        Window(
            Const("Оберiть канал\nабо додайте новий"),
            Group(
                Select(
                    text=Format("{item.name}"),  # Display channel name
                    item_id_getter=lambda channel: channel.id,  # Use channel ID
                    items="channels",  # Key from getter data
                    id="channel_select",
                    on_click=on_channel_selected,
                ),
                width=2,  # 2 buttons per row
            ),
            Row(
                Button(Const("Додати канал"), id="add_channel", on_click=add_channel),
            ),
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_main),
            ),
            state=GenerationMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=get_user_channels_data,  # Data fetcher
        )
    )