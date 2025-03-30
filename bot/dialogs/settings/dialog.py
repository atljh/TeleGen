from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column, Next, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import DialogManager

from bot.containers import Container
from .states import SettingsMenu

from .callbacks import (
    on_channel_selected,
    pay_subscription,
    go_back_to_main,
    confirm_delete_channel,

    delete_channel,
    cancel_delete_channel
)
from .flow_settings import open_flow_settings

async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {
        "channels": channels or []
    }

def create_flow_settings_window():
    return Window(
        Format(
            "🔄 <b>НАЛАШТУВАННЯ ФЛОУ</b>\n\n"
            "📢 <b>Канал:</b> {dialog_data[selected_channel].name}\n\n"
            # "ℹ️ На вашому каналі працює {dialog_data[selected_channel].subscription_type}\n"
            "🔢 <b>1520</b> (останній ID посту)\n\n"
        ),
        Column(
            Button(Const("⏱ Частота генерації"), id="generation_frequency"),
            Button(Const("🔠 Обмеження по знакам"), id="character_limit"),
            Button(Const("📌 Виділення заголовку"), id="title_highlight"),
            Button(Const("📢 Рекламний блок"), id="ad_block"),
            Button(Const("📊 Кількість постів у флоу"), id="posts_in_flow"),
            Button(Const("🗑 Видалити канал"), id="delete_channel"),
            Button(Const("📚 Налаштування джерел"), id="source_settings"),
        ),
        Row(
            SwitchTo(Const("<<< Назад"), id="back_to_main", state=SettingsMenu.channel_settings),
        ),
        state=SettingsMenu.flow_settings,
        parse_mode=ParseMode.HTML,
    )

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
                "📢 <b>Назва: {dialog_data[selected_channel].name}</b>\n"
                "🆔 <b>ID:</b> <code>{dialog_data[selected_channel].channel_id}</code>\n"
                "📅 <b>Дата додавання:</b> {dialog_data[selected_channel].created_at:%d.%m.%Y}"
            ),
            Column(
                Next(Const("Загальнi"), id="main_settings"),
                Button(Const("Налаштувати флоу"), id="flow_settings", on_click=open_flow_settings),
            ),
            Row(
                Back(Const("◀️ До списку каналів")),
                Button(Const("🏠 В головне меню"), id="go_back_to_main", on_click=go_back_to_main),
            ),
            state=SettingsMenu.channel_settings,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Format(
                "⚙️ <b>НАЛАШТУВАННЯ Загальні</b>\n\n"
                "📢 <b>Назва: {dialog_data[selected_channel].name}</b>\n"
                "📅 <b>Дата додавання:</b> {dialog_data[selected_channel].created_at:%d.%m.%Y}"

                # "ℹ️ На вашому каналі працює {dialog_data[selected_channel].subscription_type}\n\n"
            ),
            Column(
                Button(Const("⚙️ Налаштування сповіщень"), id="notification_settings"),
                Button(Const("🌍 Налаштування часового поясу"), id="timezone_settings"),
                Button(Const("😊 Емоції перед заголовком"), id="emoji_settings"),
                Button(Const("📝 Підпис каналу"), id="channel_signature"),
                Button(Const("🗑️ Видалити канал"), id="delete_channel", on_click=confirm_delete_channel),
            ),
            Row(
                Back(Const("<<< Назад")),
            ),
            state=SettingsMenu.channel_main_settings,
            parse_mode=ParseMode.HTML,
        ),
        
        Window(
            Const("⚠️ <b>Ви впевнені, що хочете видалити цей канал?</b>\n\n"
                 "Усі дані будуть втрачені без можливості відновлення."),
            Column(
                Button(Const("✅ Так, видалити"), id="confirm_delete", on_click=delete_channel),
                Button(Const("❌ Скасувати"), id="cancel_delete", on_click=cancel_delete_channel),
            ),
            state=SettingsMenu.confirm_delete,
            parse_mode=ParseMode.HTML,
        ),
    create_flow_settings_window(),
    )