from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager

from bot.containers import Container
from .states import SettingsMenu

from .callbacks import (
    on_channel_selected,
    pay_subscription,
    go_back_to_main
)

async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {
        "channels": channels or []
    }


def create_settings_dialog():
    return Dialog(
        Window(
            Const("📋 <b>Оберіть канал або додайте новий</b>"),
            Group(
                Select(
                    text=Format("📢 {item.name}"),
                    item_id_getter=lambda channel: channel.id,
                    items="channels",
                    id="channel_select",
                    on_click=on_channel_selected,
                ),
                width=2,
            ),
            Row(
                Button(Const("💳 Оплата підписки"), id="pay_subscription", on_click=pay_subscription),
            ),
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_main),
            ),
            state=SettingsMenu.main,
            parse_mode=ParseMode.HTML,
            getter=get_user_channels_data,
        ),
        Window(
            Format(
                "⚙️ <b>Налаштування каналу:</b>\n\n"
                "📢 <b>Назва:</b> {dialog_data[selected_channel].name}\n"
                "🆔 <b>ID:</b> <code>{dialog_data[selected_channel].id}</code>\n"
                # "🔘 <b>Статус:</b> {dialog_data[selected_channel].status}\n"
                "📅 <b>Дата додавання:</b> {dialog_data[selected_channel].created_at:%d.%m.%Y}"
            ),
            Column(
                Button(Const("✏️ Змінити назву"), id="edit_name"),
                Button(Const("🔄 Змінити статус"), id="toggle_status"),
                Button(Const("📊 Статистика"), id="show_stats"),
                Button(Const("🗑️ Видалити канал"), id="delete_channel"),
            ),
            Row(
                Back(Const("◀️ До списку каналів")),
                Button(Const("🏠 В головне меню"), id="go_back_to_main", on_click=go_back_to_main),
            ),
            state=SettingsMenu.channel_settings,
            parse_mode=ParseMode.HTML,
        )
    )