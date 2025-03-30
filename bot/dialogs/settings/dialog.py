from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column, Next, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
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
from .flow_settings import (
    set_character_limit,
    set_frequency,
    set_generation_frequency,
    toggle_title_highlight,
    configure_ad_block,
    set_posts_in_flow,
    open_source_settings
)

async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {
        "channels": channels or []
    }

# ================== ОКНА НАСТРОЕК ФЛОУ ==================
def create_flow_settings_window():
    return Window(
        Format(
            "🔄 <b>НАЛАШТУВАННЯ ФЛОУ</b>\n\n"
            "📢 <b>Канал:</b> {dialog_data[selected_channel].name}\n\n"
        ),
        Column(
            Button(Const("⏱ Частота генерації"), id="generation_frequency", on_click=set_generation_frequency),
            Button(Const("🔠 Обмеження по знакам"), id="character_limit", on_click=set_character_limit),
            Button(Const("📌 Виділення заголовку: {dialog_data[title_highlight]|yesno}"), 
                 id="title_highlight", on_click=toggle_title_highlight),
            Button(Const("📢 Рекламний блок"), id="ad_block", on_click=configure_ad_block),
            Button(Const("📊 Кількість постів у флоу"), id="posts_in_flow", on_click=set_posts_in_flow),
            Button(Const("📚 Налаштування джерел"), id="source_settings", on_click=open_source_settings),
            Button(Const("🗑 Видалити канал"), id="delete_channel", on_click=confirm_delete_channel),
        ),
        Row(
            Back(Const("◀️ Назад")),
        ),
        state=SettingsMenu.flow_settings,
        parse_mode=ParseMode.HTML,
    )

def create_frequency_settings_window():
    return Window(
        Const("⏱ <b>Налаштування частоти генерації</b>\n\n"
             "Оберіть як часто бот буде генерувати пости:"),
        Column(
            Button(Const("🕒 Кожні 3 години"), id="freq_3h"),
            Button(Const("🕕 Кожні 6 годин"), id="freq_6h"),
            Button(Const("🕘 Кожні 12 годин"), id="freq_12h"),
            Button(Const("🌙 Раз на день"), id="freq_24h"),
            Button(Const("✏️ Вказати власний інтервал"), id="custom_freq"),
        ),
        Row(
            Back(Const("◀️ Назад")),
        ),
        state=SettingsMenu.generation_frequency,
        parse_mode=ParseMode.HTML,
    )

def create_character_limit_window():
    return Window(
        Format(
            "🔠 <b>Обмеження по знакам</b>\n\n"
            "Поточний ліміт: {dialog_data[char_limit]} знаків\n\n"
            "Оберіть дію:"
        ),
        Column(
            Button(Const("➕ Збільшити"), id="increase_limit"),
            Button(Const("➖ Зменшити"), id="decrease_limit"),
            Button(Const("✏️ Вказати точне число"), id="set_exact_limit"),
            Button(Const("♾ Вимкнути обмеження"), id="disable_limit"),
        ),
        Row(
            Back(Const("◀️ Назад")),
        ),
        state=SettingsMenu.character_limit,
        parse_mode=ParseMode.HTML,
    )

# ================== ГЛАВНЫЙ ДИАЛОГ ==================
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
                SwitchTo(Const("Загальні"), id="main_settings", state=SettingsMenu.channel_main_settings),
                Button(Const("Налаштувати флоу"), id="flow_settings", on_click=lambda c, b, m: m.switch_to(SettingsMenu.flow_settings)),
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
        create_frequency_settings_window(),
        create_character_limit_window(),
    )