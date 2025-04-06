
from aiogram_dialog import DialogManager


async def flow_settings_getter(dialog_manager: DialogManager, **kwargs):

    flow_data = dialog_manager.dialog_data
    channel_name = flow_data.get("selected_channel").name

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
        for src in flow_data.get("sources", [])
    )
    
    return {
        "flow_name": channel_name,
        "theme": flow_data.get("channel_theme", "не вказано"),
        "source_count": len(flow_data.get("sources", [])),
        "sources": sources or "немає джерел",
        'frequency': frequency_map.get(
            flow_data.get('selected_frequency'),
            flow_data.get('selected_frequency')
        ),
        'words_limit': words_limit_map.get(
            flow_data.get('selected_words_limit'),
            flow_data.get('selected_words_limit')
        ),
        'title_highlight': 'Так' if flow_data.get('title_highlight') else 'Ні',
        'ad_time': flow_data.get('ad_time', 'Не встановлено'),
        'flow_volume': flow_data.get('flow_volume', 5),
        'signature': flow_data.get('signature', 'Без підпису'),
        'flow_id': 1
    }