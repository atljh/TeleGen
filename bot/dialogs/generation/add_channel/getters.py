from aiogram_dialog import DialogManager


async def channel_data_getter(dialog_manager: DialogManager, **kwargs):
    bot = dialog_manager.middleware_data["bot"]
    me = await bot.get_me()
    return {
        "bot_username": me.username,
        "bot_url": f"https://t.me/{me.username}?startchannel&admin=post_messages+edit_messages+delete_messages",
    }
