from aiogram_dialog import DialogManager


async def ad_time_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "message": dialog_manager.dialog_data.get("current_ad_message", "Повідомлення"),
        "current_time": dialog_manager.dialog_data.get("ad_time", "не встановлено")
    }
