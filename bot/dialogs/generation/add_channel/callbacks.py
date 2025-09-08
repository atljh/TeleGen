import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from bot.dialogs.generation.add_channel.states import AddChannelMenu
from bot.dialogs.generation.create_flow.states import CreateFlowMenu

from bot.dialogs.generation.states import GenerationMenu
from bot.containers import Container


async def on_create_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get('channel_flow')
    if channel_flow:
        await callback.answer(f"У канала {selected_channel.name} вже є Флоу")
        return
    await manager.start(
        CreateFlowMenu.select_theme,
        data={"selected_channel": selected_channel},
        mode=StartMode.RESET_STACK
    )

async def subscribe(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Функція в розробці")


async def check_admin_rights(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager
):
    bot = dialog_manager.middleware_data["bot"]

    try:
        channel_id = dialog_manager.start_data.get("channel_id")
        if not channel_id:
            raise ValueError("Channel ID not found in dialog data")

        me = await bot.get_me()
        admins = await bot.get_chat_administrators(int(channel_id))

        is_admin = any(admin.user.id == me.id for admin in admins)

        if is_admin:
            await dialog_manager.done()
            await dialog_manager.start(
                AddChannelMenu.success,
                data={
                    **dialog_manager.start_data,
                    "is_admin": True
                },
                mode=StartMode.RESET_STACK
            )
        else:
            await callback.answer("❌ Бот ще не адміністратор каналу!", show_alert=True)

    except ValueError as e:
        logging.error(f"Missing channel data: {e}")
        await callback.answer("Помилка: дані каналу не знайдено", show_alert=True)
    except Exception as e:
        logging.error(f"Error checking admin rights: {e}")
        await callback.answer("Помилка перевірки прав. Спробуйте пізніше.", show_alert=True)