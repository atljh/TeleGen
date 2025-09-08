from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Column,
    Row,
    ScrollingGroup,
    Select,
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.text import Const, Format

from .callbacks import (
    cancel_delete_source,
    character_limit,
    confirm_delete_source,
    handle_custom_volume_input,
    input_custom_volume,
    on_new_type_selected,
    on_source_link_entered,
    on_source_new_link_entered,
    on_source_selected_for_delete,
    on_source_selected_for_edit,
    on_source_type_selected,
    open_flow_settings,
    open_main_settings,
    open_source_settings,
    set_character_limit,
    set_flow_volume,
    set_frequency,
    set_generation_frequency,
    set_posts_in_flow,
    to_add_source,
    to_edit_link,
    to_edit_type,
    to_select_source_to_delete,
    to_select_source_to_edit,
    toggle_ad_block,
    toggle_title_highlight,
)
from .getters import (
    character_limit_getter,
    flow_settings_getter,
    get_current_source,
    get_source_to_delete_data,
    get_source_type_data,
    get_sources_data,
    get_sources_list,
    posts_in_flow_getter,
)
from .states import FlowSettingsMenu


def create_flow_settings_window():
    return Window(
        Format(
            """
        <b>Канал:</b> {channel_name}

        <b>Параметри Flow</b>
        - <b>Тематика:</b> {theme}
        - <b>Джерела ({source_count}):</b>
            <b>{sources}</b>
        - <b>Частота генерації:</b> {frequency}
        - <b>Кількість знаків:</b> {words_limit}
        - <b>Кількість постів у флоу:</b> {flow_volume}
        - <b>Виділення заголовка:</b> {title_highlight}
        - <b>Підпис до постів:</b> {signature}
        """
        ),
        Column(
            Button(
                Const("⏱ Частота генерації"),
                id="generation_frequency",
                on_click=set_generation_frequency,
            ),
            Button(
                Const("🔠 Обмеження по символам"),
                id="character_limit",
                on_click=character_limit,
            ),
            Button(
                Format("📌 Виділення заголовку: {title_highlight}"),
                id="title_highlight",
                on_click=toggle_title_highlight,
            ),
            # Button(Const("📢 Рекламний блок"), id="ad_block", on_click=configure_ad_block),
            Button(
                Const("📊 Кількість постів у флоу"),
                id="posts_in_flow",
                on_click=set_posts_in_flow,
            ),
            Button(
                Const("📚 Налаштування джерел"),
                id="source_settings",
                on_click=open_source_settings,
            ),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_main_settings", on_click=open_main_settings
            ),
        ),
        LinkPreview(is_disabled=True),
        state=FlowSettingsMenu.flow_settings,
        parse_mode=ParseMode.HTML,
        getter=flow_settings_getter,
    )


def create_ad_block_settings_window():
    return Window(
        Const("📢 Налаштування рекламного блоку</b>"),
        Column(
            Button(
                Const("✅ Включити рекламу"), id="enable_ads", on_click=toggle_ad_block
            ),
            Button(
                Const("❌ Вимкнути рекламу"), id="disable_ads", on_click=toggle_ad_block
            ),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.ad_block_settings,
        parse_mode=ParseMode.HTML,
    )


def create_frequency_settings_window():
    return Window(
        Const(
            "⏱ <b>Налаштування частоти генерації</b>\n\n"
            "Оберіть як часто бот буде генерувати пости:"
        ),
        Column(
            Button(Const("Кожну годину"), id="freq_1h", on_click=set_frequency),
            Button(Const("Кожні 12 годин"), id="freq_12h", on_click=set_frequency),
            Button(Const("Раз на день"), id="freq_24h", on_click=set_frequency),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.generation_frequency,
        parse_mode=ParseMode.HTML,
    )


def create_character_limit_window():
    return Window(
        Format(
            "🔠 <b>Обмеження по знакам</b>\n\n"
            "Поточний ліміт: {char_limit} знаків\n\n"
            "Оберіть дію:"
        ),
        Column(
            Button(Const("До 100"), id="limit_100", on_click=set_character_limit),
            Button(Const("До 300"), id="limit_300", on_click=set_character_limit),
            Button(Const("До 1000"), id="limit_1000", on_click=set_character_limit),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.character_limit,
        parse_mode=ParseMode.HTML,
        getter=character_limit_getter,
    )


def create_posts_in_flow_window():
    return Window(
        Format(
            "📊 <b>Кількість постів у флоу</b>\n\n"
            "Поточне значення: <code>{posts_count}</code>\n\n"
            "Вибери одне з типових значень або введи своє:"
        ),
        Column(
            Button(Const("5"), id="volume_5", on_click=set_flow_volume),
            Button(Const("10"), id="volume_10", on_click=set_flow_volume),
            Button(Const("20"), id="volume_20", on_click=set_flow_volume),
            Button(
                Const("🔢 Ввести вручну"),
                id="custom_volume_input",
                on_click=input_custom_volume,
            ),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.posts_in_flow,
        parse_mode=ParseMode.HTML,
        getter=posts_in_flow_getter,
    )


def create_sources_dialog():
    return Window(
        Format(
            "<b>Управління джерелами</b>\n\n"
            "Кількість джерел: {sources_count}\n\n"
            "{sources_list}"
        ),
        Column(
            Button(Const("➕ Додати джерело"), id="add_source", on_click=to_add_source),
            Button(
                Const("✏️ Редагувати джерело"),
                id="edit_source",
                on_click=to_select_source_to_edit,
            ),
            Button(
                Const("🗑 Видалити джерело"),
                id="delete_source",
                on_click=to_select_source_to_delete,
            ),
        ),
        Button(Const("🔙 Назад"), id="back_to_settings", on_click=open_flow_settings),
        state=FlowSettingsMenu.source_settings,
        parse_mode=ParseMode.HTML,
        getter=get_sources_data,
    )


def create_custom_volume_window():
    return Window(
        Format(
            "🔢 <b>Введи свою кількість постів у флоу</b>\n\nВкажи число від 1 до 100:"
        ),
        TextInput(
            id="handle_custom_volume_input",
            on_success=handle_custom_volume_input,
            filter=volume_filter,
        ),
        Row(
            Button(
                Const("🔙 Назад"),
                id="back_to_flow_window",
                on_click=lambda c, b, m: m.switch_to(FlowSettingsMenu.posts_in_flow),
            ),
        ),
        state=FlowSettingsMenu.waiting_for_custom_volume,
        parse_mode=ParseMode.HTML,
    )


async def volume_filter(message: Message):
    text = message.text
    if not text.isdigit():
        await message.answer("❗ Значення має бути числом")
        return False
    return True


# =======================================ADD FLOW===========================================


async def link_filter(message: Message):
    text = message.text
    if not (text.startswith("http://") or text.startswith("https://")):
        await message.answer("❗ Посилання має починатися з http:// або https://")
        return False
    return True


def create_select_source_type():
    return Window(
        Const("📚 Виберіть тип джерела:"),
        Column(
            Button(
                Const("📷 Instagram"),
                id="source_instagram",
                on_click=on_source_type_selected,
            ),
            Button(
                Const("🌐 Веб-сайт"), id="source_web", on_click=on_source_type_selected
            ),
            Button(
                Const("✈️ Telegram"),
                id="source_telegram",
                on_click=on_source_type_selected,
            ),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.add_source_type,
        parse_mode=ParseMode.HTML,
    )


def create_input_source_link():
    return Window(
        Format(
            "🔗 Введіть посилання для {source_type}:\n\n"
            "Приклад: <code>{link_example}</code>"
        ),
        TextInput(
            id="source_link_input",
            on_success=on_source_link_entered,
            filter=link_filter,
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.add_source_link,
        parse_mode=ParseMode.HTML,
        getter=get_source_type_data,
    )


# =======================================EDIT FLOW===========================================


def create_select_edit_source():
    return Window(
        Const("✏️ Оберіть джерело для редагування:"),
        ScrollingGroup(
            Select(
                Format("{item[type]} - {item[link]}"),
                id="select_edit_source",
                item_id_getter=lambda item: item["idx"],
                items="sources",
                on_click=on_source_selected_for_edit,
            ),
            id="sources_scroll",
            width=1,
            height=5,
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.edit_select_source,
        parse_mode=ParseMode.HTML,
        getter=get_sources_list,
    )


def create_edit_source():
    return Window(
        Format("Редагування джерела:\nТип: {source_type}\nПосилання: {source_link}"),
        Column(
            Button(Const("✏️ Змінити посилання"), id="edit_link", on_click=to_edit_link),
            Button(Const("♻️ Змінити тип"), id="edit_type", on_click=to_edit_type),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.edit_source,
        getter=get_current_source,
    )


def create_edit_source_type():
    return Window(
        Const("📚 Виберіть тип джерела:"),
        Column(
            Button(
                Const("📷 Instagram"),
                id="source_instagram",
                on_click=on_new_type_selected,
            ),
            Button(
                Const("🌐 Веб-сайт"), id="source_web", on_click=on_new_type_selected
            ),
            Button(
                Const("✈️ Telegram"),
                id="source_telegram",
                on_click=on_new_type_selected,
            ),
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.edit_source_type,
        parse_mode=ParseMode.HTML,
    )


def create_edit_source_link():
    return Window(
        Format(
            "🔗 Введіть посилання для {source_type}:\n\n"
            "Приклад: <code>{link_example}</code>"
        ),
        TextInput(
            id="source_link_input",
            on_success=on_source_new_link_entered,
            filter=link_filter,
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.edit_source_link,
        parse_mode=ParseMode.HTML,
        getter=get_source_type_data,
    )


# =======================================DELETE FLOW===========================================


def create_select_delete_source():
    return Window(
        Const("Оберіть джерело для видалення:"),
        ScrollingGroup(
            Select(
                Format("{item[type]} - {item[link]}"),
                id="sources_select",
                item_id_getter=lambda item: item["id"],
                items="sources",
                on_click=on_source_selected_for_delete,
            ),
            width=1,
            height=5,
            id="delete_select",
        ),
        Row(
            Button(
                Const("🔙 Назад"), id="open_flow_settings", on_click=open_flow_settings
            ),
        ),
        state=FlowSettingsMenu.select_source_to_delete,
        getter=get_sources_data,
    )


def create_confirm_delete_source():
    return Window(
        Format(
            "Ви впевнені, що хочете видалити джерело {source_to_delete[type]} - {source_to_delete[link]}?"
        ),
        Row(
            Button(
                Const("✅ Так"), id="confirm_delete", on_click=confirm_delete_source
            ),
            Button(Const("❌ Ні"), id="cancel_delete", on_click=cancel_delete_source),
        ),
        state=FlowSettingsMenu.confirm_delete_source,
        getter=get_source_to_delete_data,
    )


def create_flow_settings_dialog():
    return Dialog(
        create_flow_settings_window(),
        create_frequency_settings_window(),
        create_character_limit_window(),
        # create_ad_block_settings_window(),
        create_posts_in_flow_window(),
        create_custom_volume_window(),
        create_sources_dialog(),
        create_select_source_type(),
        create_input_source_link(),
        create_select_edit_source(),
        create_edit_source(),
        create_edit_source_type(),
        create_edit_source_link(),
        create_select_delete_source(),
        create_confirm_delete_source(),
    )
