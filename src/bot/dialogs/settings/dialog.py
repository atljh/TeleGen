from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Column,
    Group,
    Row,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.text import Const, Format

from bot.containers import Container
from bot.dialogs.settings.payment.states import PaymentMenu
from bot.utils.constants.buttons import BACK_BUTTON

from .callbacks import (
    cancel_delete_channel,
    confirm_delete_channel,
    delete_channel,
    handle_emoji_input,
    handle_sig_input,
    on_channel_selected,
    open_emoji_settings,
    open_notification_settings,
    open_settings,
    open_signature_editor,
    open_timezone_settings,
    set_timezone,
    toggle_notification,
)
from .flow_settings.callbacks import start_flow_settings
from .getters import (
    emoji_getter,
    notification_getter,
    selected_channel_getter,
    timezone_getter,
)
from .states import SettingsMenu


async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {"channels": channels or []}


def create_settings_dialog():
    return Dialog(
        Window(
            Const("<b>Оберіть канал або додайте новий</b>"),
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
                Button(
                    Const("💳 Оплата підписки"),
                    id="pay_subscription",
                    on_click=lambda c, b, m: m.start(PaymentMenu.main),
                ),
            ),
            state=SettingsMenu.main,
            parse_mode=ParseMode.HTML,
            getter=get_user_channels_data,
        ),
        Window(
            Format(
                "<b>Налаштування каналу:</b>\n\n"
                "<b>Назва: {selected_channel.name}</b>\n"
                "<b>Флоу: {channel_flow}</b>"
            ),
            Column(
                SwitchTo(
                    Const("Загальні"),
                    id="main_settings",
                    state=SettingsMenu.channel_main_settings,
                ),
                Button(
                    Const("Налаштувати флоу"),
                    id="flow_settings",
                    on_click=start_flow_settings,
                ),
            ),
            Row(
                Back(BACK_BUTTON),
            ),
            state=SettingsMenu.channel_settings,
            parse_mode=ParseMode.HTML,
            getter=selected_channel_getter,
        ),
        Window(
            Format(
                "<b>НАЛАШТУВАННЯ Загальні</b>\n\n"
                "<b>Назва: {selected_channel.name}</b>\n"
                "<b>Флоу: {channel_flow}</b>"
            ),
            Column(
                Button(
                    Const("⚙️ Налаштування сповіщень"),
                    id="notification_settings",
                    on_click=open_notification_settings,
                ),
                Button(
                    Const("🌍 Налаштування часового поясу"),
                    id="timezone_settings",
                    on_click=open_timezone_settings,
                ),
                Button(
                    Const("😊 Емоції перед заголовком"),
                    id="emoji_settings",
                    on_click=open_emoji_settings,
                ),
                Button(
                    Const("📝 Підпис каналу"),
                    id="channel_signature",
                    on_click=open_signature_editor,
                ),
                Button(
                    Const("🗑️ Видалити канал"),
                    id="delete_channel",
                    on_click=confirm_delete_channel,
                ),
            ),
            Row(
                Back(BACK_BUTTON),
            ),
            state=SettingsMenu.channel_main_settings,
            parse_mode=ParseMode.HTML,
            getter=selected_channel_getter,
        ),
        Window(
            Format(
                "<b>НАЛАШТУВАННЯ ПІДПИСУ КАНАЛУ</b>\n\n"
                "Поточний підпис: "
                "{signature}\n\n"
                "Введiть новий підпис: "
            ),
            Row(
                Back(BACK_BUTTON),
            ),
            LinkPreview(is_disabled=True),
            MessageInput(handle_sig_input),
            state=SettingsMenu.edit_signature,
            parse_mode=ParseMode.HTML,
            getter=selected_channel_getter,
        ),
        Window(
            Format("🔔 <b>Налаштування сповіщень для {channel_name}</b>\n\n"),
            Column(
                Button(
                    Format("{notifications_enabled}"),
                    id="notifications_toggle",
                    on_click=toggle_notification,
                )
            ),
            Button(BACK_BUTTON, id="open_settings", on_click=open_settings),
            LinkPreview(is_disabled=True),
            state=SettingsMenu.notification_settings,
            parse_mode=ParseMode.HTML,
            getter=notification_getter,
        ),
        Window(
            Format(
                "🌍 <b>Налаштування часового поясу для {channel_name}</b>\n\n"
                "Поточний часовий пояс: {current_timezone}\n\n"
                "Оберіть новий часовий пояс:"
            ),
            Column(
                Button(
                    Const("🇺🇦 Київ (UTC+2)"), id="tz_europe_kiev", on_click=set_timezone
                ),
                Button(
                    Const("🇪🇺 Лондон (UTC+0)"),
                    id="tz_europe_london",
                    on_click=set_timezone,
                ),
                Button(
                    Const("🇺🇸 Нью-Йорк (UTC-4)"),
                    id="tz_america_new_york",
                    on_click=set_timezone,
                ),
            ),
            Button(BACK_BUTTON, id="open_settings", on_click=open_settings),
            state=SettingsMenu.timezone_settings,
            parse_mode=ParseMode.HTML,
            getter=timezone_getter,
        ),
        Window(
            Format(
                "😊 <b>Налаштування емодзі для {channel_name}</b>\n\n"
                "Поточне емодзі: <b>{title_emoji}</b>\n\n"
                "Введіть новий емодзі або відправте пусте повідомлення для видалення:"
            ),
            MessageInput(handle_emoji_input),
            Button(BACK_BUTTON, id="open_settings", on_click=open_settings),
            state=SettingsMenu.emoji_settings,
            parse_mode=ParseMode.HTML,
            getter=emoji_getter,
        ),
        Window(
            Const(
                "⚠️ <b>Ви впевнені, що хочете видалити цей канал?</b>\n\n"
                "Усі дані будуть втрачені без можливості відновлення"
            ),
            Column(
                Button(
                    Const("✅ Так, видалити"),
                    id="confirm_delete",
                    on_click=delete_channel,
                ),
                Button(
                    Const("❌ Скасувати"),
                    id="cancel_delete",
                    on_click=cancel_delete_channel,
                ),
            ),
            state=SettingsMenu.confirm_delete,
            parse_mode=ParseMode.HTML,
        ),
    )
