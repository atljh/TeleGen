from aiogram import F
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Column, Row, Next, Back, Select
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from aiogram.enums import ParseMode

from bot.dialogs.generation.callbacks import on_force_generate
from dialogs.settings.flow_settings.callbacks import start_flow_settings
from bot.dialogs.generation.create_flow.states import CreateFlowMenu
from .getters import (
    ad_time_getter,
    flow_volume_getter,
    signature_getter,
    flow_confirmation_getter,
    source_link_getter,
    source_confirmation_getter,
    source_type_getter
)
from .callbacks import(
    start_generation_process,
    to_channel,
    to_select_frequency,
    
    on_channel_theme_selected,
    on_custom_theme_entered,
    to_custom_theme_input,

    on_once_a_day,
    on_once_a_12,
    on_once_an_hour,

    on_to_100,
    on_to_300,
    on_to_1000,

    on_source_link_entered,
    on_source_type_selected,
    on_source_link_entered,
    add_more_sources,
    
    confirm_title_highlight,
    reject_title_highlight,
    
    handle_time_input,
    reset_ad_time,
    
    on_volume_selected,
    open_custom_volume_input,
    handle_custom_volume_input,
    
    handle_signature_input,
    skip_signature
)

def create_flow_dialog():
    return Dialog(
        Window(
            Format(
                "**Етап 1 из 7**\n\n"
                "**Оберіть тему каналу з існуючих або додайте**"
            ),
            Column(
                Button(Const("Спортивний канал"), id="Sport", on_click=on_channel_theme_selected),
                Button(Const("Кулінарний канал"), id="Cooking", on_click=on_channel_theme_selected),
                Button(Const("Регіональний канал"), id="Regional", on_click=on_channel_theme_selected),
                Button(Const("✏️ Задати тему самостійно"), id="custom_theme", on_click=to_custom_theme_input),
            ),
            Row(
                Button(Const("🔙 Назад"), id="to_channel", on_click=to_channel),
            ),
            state=CreateFlowMenu.select_theme,
            parse_mode=ParseMode.MARKDOWN_V2
        ),
        Window(
            Format(
                "**Етап 2 из 7**\n\n"
                "📌 **Оберіть тип джерела**\n\n"
                "Доступні варіанти:\n\n"
                "🛒 **Вже обрані джерела:**\n"
                "{selected_sources}"
            ),
            Column(
                Button(Const("📷 Instagram"), id="instagram", on_click=on_source_type_selected),
                Button(Const("👍 Facebook"), id="facebook", on_click=on_source_type_selected),
                Button(Const("🌐 Web-сайт"), id="web", on_click=on_source_type_selected),
                Button(Const("✈️ Telegram"), id="telegram", on_click=on_source_type_selected),
            ),
            Row(
                Back(Const("🔙 Назад")),
                Button(Const("🔜 Далі"), id="next", when="has_selected_sources", on_click=to_select_frequency),
            ),
            state=CreateFlowMenu.select_source,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=source_type_getter
        ),
        Window(
            Format("🔗 **Додавання {source_name}**\n\n"
                  "Відправте посилання за шаблоном:\n"
                  "<code>{link_example}</code>"),
            TextInput(
                id="source_link_input",
                on_success=on_source_link_entered,
                filter=F.text & ~F.text.startswith('/')
            ),
            Row(
                Back(Const("🔙 Назад")),
                # Button(Const("📋 Мої джерела"), id="my_sources", on_click=show_my_sources),
            ),
            state=CreateFlowMenu.add_source_link,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=source_link_getter
        ),
        Window(
            Format("✅ **Джерело додано**\n\n"
                  "Тип: {source_type}\n"
                  "Посилання: {source_link}\n\n"
                  "Додати ще одне джерело?"),
            Column(
                Button(Const("➕ Так"), id="add_more_sources", on_click=add_more_sources),
                Next(Const("🔜 Ні, продовжити"), id="continue_flow"),
            ),
            state=CreateFlowMenu.source_confirmation,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=source_confirmation_getter
        ),
        Window(
            Const(
                "**Етап 3 из 7**\n\n"
                "**Оберіть частоту генерацii**"
            ),
            Column(
                Button(Const("Раз на день"), id="daily", on_click=on_once_a_day),
                Button(Const("Раз на 12 годин"), id="12h", on_click=on_once_a_12),
                Button(Const("Раз на годину"), id="hourly", on_click=on_once_an_hour),
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            state=CreateFlowMenu.select_frequency,
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
        Window(
            Const(
                "**Етап 4 из 7**\n\n"
                "**Оберіть обмеження по кiлькостi знакiв в постах**"
            ),
            Column(
                Button(Const("До 100"), id="to_100", on_click=on_to_100),
                Button(Const("До 300"), id="to_300", on_click=on_to_300),
                Button(Const("До 1000"), id="to_1000", on_click=on_to_1000),
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            state=CreateFlowMenu.select_words_limit,
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
        Window(
            Const(
                "**Етап 5 из 7**\n\n"
                "✏️ **Чи потрібно виділяти заголовок?**\n\n"
            ),
            Column(
                Button(
                    Const("✅ Так"),
                    id="highlight_yes",
                    on_click=confirm_title_highlight
                ),
                Button(
                    Const("❌ Ні"),
                    id="highlight_no",
                    on_click=reject_title_highlight
                ),
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            state=CreateFlowMenu.title_highlight_confirm,
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
        # Window(
        #     Format("⏰ **Налаштування рекламного топу**\n\n"
        #       "Введіть час рекламного топу в форматі\n"
        #       "<code>hh:mm</code>\n\n"
        #       "Поточне повідомлення:\n"
        #       "{message}"),
        #     MessageInput(
        #         handle_time_input,
        #         filter=F.text & ~F.text.startswith('/')
        #     ),
        #     Row(
        #         Back(Const("🔙 Назад")),
        #         Button(Const("🔄 Скинути"), id="reset_time", on_click=reset_ad_time),
        #     ),
        #     state=CreateFlowMenu.ad_time_settings,
        #     parse_mode=ParseMode.MARKDOWN_V2,
        #     getter=ad_time_getter
        # ),
        Window(
            Format(
                "**Етап 6 из 7**\n\n"
                "📊 **Налаштування об'єму флоу**\n\n"
                "Оберіть кількість останніх постів,\n"
                "яку треба зберігати у флоу:\n\n"
                "Поточне значення: {current_value}"),
            Column(
                Select(
                    text=Format("{item}"),
                    items="volume_options",
                    item_id_getter=lambda x: x,
                    id="volume_select",
                    on_click=on_volume_selected,
                ),
            ),
            Row(
                Button(
                    Const("✏️ Вказати своє число"), 
                    id="custom_volume", 
                    on_click=open_custom_volume_input
                ),
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            state=CreateFlowMenu.flow_volume_settings,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=flow_volume_getter
        ),
        Window(
            Const(
                "✏️ **Введіть власне число**\n\n"
                "Діапазон: 1-50\n\n"
                "Або натисніть 'Назад'"),
            MessageInput(
                handle_custom_volume_input,
                filter=F.text & ~F.text.startswith('/')
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            state=CreateFlowMenu.custom_volume_input,
            parse_mode=ParseMode.MARKDOWN_V2
        ),
        Window(
            Format(
                "**Етап 7 из 7**\n\n"
                "✍️ **Налаштування підпису до постів**\n\n"
                "Поточний підпис:\n"
                "<code>{current_signature}</code>\n\n"
                "Відправте новий підпис або натисніть 'Пропустити'\n"
                "<i>Підтримка emoji та HTML-розмітки</i>"),
            MessageInput(
                handle_signature_input,
                filter=F.text & ~F.text.startswith('/')
            ),
            Row(
                Button(Const("⏩ Пропустити"), id="skip_signature", on_click=skip_signature),
                Back(Const("🔙 Назад")),
            ),
            state=CreateFlowMenu.signature_settings,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=signature_getter
        ),
        Window(
            Format(
                "🎉 **Вітаю! Ваш флоу успішно створений!**\n\n"
                "🔧 Ви можете змінити його параметри в налаштуваннях.\n\n"
                "📌 **Параметри Flow \"{flow_name}\":**\n"
                "▪️ **Тематика:** {theme}\n"
                "▪️ **Джерела ({source_count}):**\n  {sources}\n"
                "▪️ **Частота генерації:** {frequency}\n"
                "▪️ **Кількість знаків:** {words_limit}\n"
                "▪️ **Кількість постiв у флоу:** {flow_volume}\n"
                "▪️ **Виділення заголовка:** {title_highlight}\n"
                "▪️ **Підпис до постів:** {signature}\n\n"
            ),
            Column(
                Button(Const("Налаштування Flow"), id="to_settings", on_click=start_flow_settings),
                Button(Const("Почати генерацiю"), id="start_generation", on_click=start_generation_process),
            ),
            state=CreateFlowMenu.confirmation,
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=flow_confirmation_getter
        ),
        Window(
            Format("✏️ **Введіть власну тему каналу:**"),
            TextInput(
                id="custom_theme_input",
                on_success=on_custom_theme_entered,
                filter=F.text & ~F.text.startswith('/')
            ),
            Back(Const("🔙 Назад")),
            state=CreateFlowMenu.input_custom_theme,
            parse_mode=ParseMode.MARKDOWN_V2
        ),
    )