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

async def posts_in_flow_getter(dialog_manager: DialogManager, **kwargs):
    volume_map = {
        "volume_5": "5",
        "volume_10": "10",
        "volume_20": "20"
    }
    if "channel_flow" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["channel_flow"] = dialog_manager.start_data["channel_flow"]
    return {
        "posts_count": dialog_manager.dialog_data["channel_flow"].flow_volume
    }

async def get_sources_data(dialog_manager: DialogManager, **kwargs):
    flow_data = (
        dialog_manager.dialog_data.get("channel_flow") 
        or dialog_manager.start_data.get("channel_flow")
    )
    
    sources = getattr(flow_data, "sources", [])
    
    formatted_sources = [
        {
            "id": str(src.get("id", idx+1)),
            "type": src.get("type", "Невідомий тип"),
            "link": src.get("link", "Без посилання"),
            "display": f"{src.get('type')}: {src.get('link')}"
        }
        for idx, src in enumerate(sources)
    ]
    if not sources:
        sources_text = "<i>Джерела відсутні</i>"
    else:
        sources_text = "\n".join(
            f"{idx+1}. <b>{src['type']}</b>: <code>{src['link']}</code>"
            for idx, src in enumerate(sources)
        )

    return {
        "sources": formatted_sources,
        "sources_count": len(sources),
        "sources_list": sources_text
    }


async def get_source_type(dialog_manager: DialogManager, **kwargs):
    return {
        "source_type": dialog_manager.dialog_data.get("new_source_type", "джерела")
    }


async def get_current_source(dialog_manager: DialogManager, **kwargs):
    try:
        flow = (
            dialog_manager.dialog_data.get("channel_flow") 
            or dialog_manager.start_data.get("channel_flow")
        )
        
        if not flow or not hasattr(flow, "sources"):
            raise ValueError("Дані флоу не знайдено")
            
        source_idx = dialog_manager.dialog_data.get("editing_source_idx")
        if source_idx is None:
            raise ValueError("Індекс джерела не вказано")
            
        sources = flow.sources
        if not isinstance(sources, list) or source_idx >= len(sources):
            raise ValueError("Невірний індекс джерела")
            
        source = sources[source_idx]
        return {
            "source_type": source.get("type", "Невідомий тип"),
            "source_link": source.get("link", "Без посилання"),
            "source_idx": source_idx
        }
        
    except Exception as e:
        logging.error(f"Помилка при отриманні джерела: {e}")
        return {
            "source_type": "Помилка",
            "source_link": str(e),
            "source_idx": -1
        }

async def get_sources_for_selection(dialog_manager: DialogManager, **kwargs):
    flow = (
        dialog_manager.dialog_data.get("channel_flow") 
        or dialog_manager.start_data.get("channel_flow")
    )
    
    sources = getattr(flow, "sources", [])
    
    formatted_sources = [
        {"type": src.get("type", "?"), "link": src.get("link", "?"), "idx": idx}
        for idx, src in enumerate(sources)
    ]
    
    return {
        "formatted_sources": formatted_sources,
        "has_sources": bool(sources)
    }

async def get_source_type_data(dialog_manager: DialogManager, **kwargs):
    source_type = dialog_manager.dialog_data.get("new_source_type", "джерела")
    examples = {
        "instagram": "https://instagram.com/username",
        "web": "https://example.com",
        "telegram": "https://t.me/channelname"
    }
    return {
        "source_type": source_type,
        "link_example": examples.get(source_type, "https://example.com")
    }