from aiogram_dialog import DialogManager


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
    return {
        "current_signature": dialog_manager.dialog_data.get("signature", "Підпис не встановлено")
    }

async def flow_confirmation_getter(dialog_manager: DialogManager, **kwargs):
    flow_data = dialog_manager.dialog_data.get("created_flow", {})
    
    sources = "\n".join(
        f"{src['type']} - {src['link']}" 
        for src in flow_data.get("sources", [])
    )
    
    return {
        "flow_name": flow_data.get("name", "Новий флоу"),
        "theme": flow_data.get("theme", "не вказано"),
        "source_count": len(flow_data.get("sources", [])),
        "sources": sources or "немає джерел",
        "frequency": flow_data.get("frequency", "не встановлено"),
        "char_limit": flow_data.get("char_limit", "не встановлено"),
        "title_highlight": "так" if flow_data.get("title_highlight") else "ні",
        "signature": flow_data.get("signature", "немає підпису"),
        "flow_id": flow_data.get("id", "---")
    }