import logging
from aiogram_dialog import DialogManager


async def flow_settings_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}

    flow_data = (
        start_data.get("channel_flow", False)
        or dialog_data.get("channel_flow", False)
    )

    channel_data = (
        start_data.get("selected_channel", False)
        or dialog_data.get("selected_channel", False)
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
        f"{src['type']} - {src['link']}" 
        for src in flow_data.sources
    )
    
    return {
        "channel_name": channel_data.name,
        "theme": flow_data.theme,
        "source_count": len(flow_data.sources),
        "sources": sources or "немає джерел",
        'frequency': frequency_map.get(
            flow_data.frequency,
            flow_data.frequency
        ),
        'words_limit': words_limit_map.get(
            flow_data.content_length,
            flow_data.content_length
        ),
        'title_highlight': 'Так' if flow_data.title_highlight else 'Ні',
        'ad_time': flow_data.ad_time,
        'flow_volume': flow_data.flow_volume,
        'signature': flow_data.signature,
    }