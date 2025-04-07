import logging
from aiogram_dialog import DialogManager


async def flow_settings_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}

    flow_data = (
        dialog_data.get("channel_flow")
        or start_data.get("channel_flow")
    )
    
    channel_data = (
        dialog_data.get("selected_channel")
        or start_data.get("selected_channel")
    )

    frequency_map = {
        'daily': 'Раз на день',
        '12h': 'Раз на 12 годин',
        'hourly': 'Раз на годину',
    }
    
    words_limit_map = {
        'to_100': 'До 100 слів',
        'to_300': 'До 300 слів',
        'to_500': 'До 500 слів',
        'to_1000': 'До 1000 слів',
    }

    sources = "\n".join(
        f"• {src['type']} - {src['link']}" 
        for src in getattr(flow_data, "sources", [])
    ) if getattr(flow_data, "sources", []) else "немає джерел"

    return {
        "channel_name": getattr(channel_data, "name", "Невідомий канал"),
        "theme": getattr(flow_data, "theme", "Не вказано"),
        "source_count": len(getattr(flow_data, "sources", [])),
        "sources": sources,
        "frequency": frequency_map.get(
            getattr(flow_data, "frequency", "daily"),
            getattr(flow_data, "frequency", "daily")
        ),
        "words_limit": words_limit_map.get(
            getattr(flow_data, "content_length", "to_1000"),
            getattr(flow_data, "content_length", "to_1000")
        ),
        "title_highlight": "Так" if getattr(flow_data, "title_highlight", False) else "Ні",
        "flow_volume": getattr(flow_data, "flow_volume", 5),
        "signature": getattr(flow_data, "signature", "Немає підпису"),
    }


async def character_limit_getter(dialog_manager: DialogManager, **kwargs):
    limit_map = {
        "to_100": "100",
        "to_300": "300",
        "to_1000": "1000"
    }
    if "channel_flow" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["channel_flow"] = dialog_manager.start_data["channel_flow"]
    return {
        "char_limit": limit_map.get(dialog_manager.dialog_data["channel_flow"].content_length)
    }

