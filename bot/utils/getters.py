import logging
from datetime import datetime
from aiogram_dialog import DialogManager


async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}
    logging.info(dialog_data)
    selected_channel = start_data.get("selected_channel") or dialog_data.get(
        "selected_channel"
    )
    channel_flow = start_data.get("channel_flow", False) or dialog_data.get(
        "channel_flow", False
    )

    if not selected_channel:
        return {
            "channel_name": "Канал не вибрано",
            "channel_id": "N/A",
            "created_at": datetime.now(),
            "channel_flow": "Вiдсутнiй",
        }

    dialog_manager.dialog_data["selected_channel"] = selected_channel
    dialog_manager.dialog_data["channel_flow"] = channel_flow

    return {
        "channel_name": selected_channel.name,
        "channel_id": selected_channel.channel_id,
        "created_at": selected_channel.created_at,
        "channel_flow": "Присутнiй" if channel_flow else "Вiдсутнiй",
    }
