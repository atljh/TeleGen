import html
from aiogram_dialog import DialogManager
import logging

async def ad_time_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "message": dialog_manager.dialog_data.get("current_ad_message", "Повідомлення"),
        "current_time": dialog_manager.dialog_data.get("ad_time", "не встановлено")
    }

async def flow_volume_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "current_value": dialog_manager.dialog_data.get("flow_volume", "не встановлено"),
        "volume_options": ["5", "10", "20"]
    }
async def signature_getter(dialog_manager: DialogManager, **kwargs):
    dialog_data = dialog_manager.dialog_data
    
    current_signature = dialog_data.get("display_signature", "Підпис ще не встановлено")
    
    return {
        "current_signature": current_signature,
    }

async def flow_confirmation_getter(dialog_manager: DialogManager, **kwargs):
    flow_data = dialog_manager.dialog_data.get("created_flow", {})
    

    return {
        "frequency": flow_data.get("frequency", "не встановлено"),
        "char_limit": flow_data.get("char_limit", "не встановлено"),
        "title_highlight": "так" if flow_data.get("title_highlight") else "ні",
        "signature": flow_data.get("signature", "немає підпису"),
        "flow_id": flow_data.get("id", "---")
    }


async def source_type_getter(dialog_manager: DialogManager, **kwargs):
    dialog_data = dialog_manager.dialog_data
    selected_channel = dialog_manager.start_data.get("selected_channel") 

    dialog_manager.dialog_data["selected_channel"] = selected_channel
    selected_sources = dialog_data.get("sources", [])
    sources_list = "\n".join(
        f"▫️ {source.get('type', '')} - {source.get('link', '')}"
        for source in selected_sources
    ) if selected_sources else "┄ Джерела ще не додані ┄"
    
    return {
        "selected_sources": sources_list,
        "has_selected_sources": bool(selected_sources)
    }

async def source_link_getter(dialog_manager: DialogManager, **kwargs):
    source_type = dialog_manager.dialog_data.get("selected_source_type", "")
    source_name = {
        "instagram": "Instagram",
        "facebook": "Facebook",
        "web": "Web-сайт",
        "telegram": "Telegram"
    }.get(source_type, "джерело")
    
    examples = {
        "instagram": "https://instagram.com/username",
        "facebook": "https://facebook.com/page",
        "web": "https://example.com",
        "telegram": "https://t.me/channel"
    }
    
    return {
        "source_name": source_name,
        "link_example": examples.get(source_type, "https://...")
    }

async def source_confirmation_getter(dialog_manager: DialogManager, **kwargs):
    dialog_data = dialog_manager.dialog_data
    
    source_type = dialog_data.get("source_type", "Невідомий")
    source_link = dialog_data.get("source_link", "Не вказано")
    
    return {
        "source_type": str(source_type),
        "source_link": str(source_link)
    }

async def flow_confirmation_getter(dialog_manager: DialogManager, **kwargs):

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
