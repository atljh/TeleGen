import asyncio
import re
import logging
import subprocess
import sys
from html import escape as escape_html
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import TextInput
from aiogram.enums import ParseMode

from bot.database.models import ContentLength, GenerationFrequency
from bot.database.exceptions import ChannelNotFoundError

from bot.dialogs.generation.callbacks import show_generated_posts
from bot.dialogs.generation.create_flow.states import CreateFlowMenu
from bot.containers import Container
from bot.utils.formatting import parse_entities_to_html

logger = logging.getLogger(__name__)

from bot.dialogs.generation.states import GenerationMenu


async def to_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get(
        "selected_channel", manager.start_data["selected_channel"]
    )
    await manager.start(
        GenerationMenu.channel_main,
        mode=StartMode.RESET_STACK,
        data={"selected_channel": selected_channel},
    )


async def to_select_frequency(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CreateFlowMenu.select_frequency)


# ==================THEME======================


async def on_channel_theme_selected(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    theme = button.widget_id  # "sport_channel", "cooking_channel"
    manager.dialog_data["channel_theme"] = theme
    await manager.switch_to(CreateFlowMenu.select_source)


async def to_custom_theme_input(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CreateFlowMenu.input_custom_theme)


async def on_custom_theme_entered(
    message: Message, widget: TextInput, manager: DialogManager, text: str
):
    manager.dialog_data["channel_theme"] = text
    await manager.switch_to(CreateFlowMenu.select_source)


# ==================SOURCE======================


async def on_source_type_selected(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    dialog_data = manager.dialog_data

    button_text = (
        button.text.value if hasattr(button.text, "value") else str(button.text)
    )

    dialog_data["selected_source_type"] = button.widget_id
    dialog_data["selected_source_name"] = button_text

    if "sources" not in dialog_data:
        dialog_data["sources"] = []

    await manager.switch_to(CreateFlowMenu.add_source_link)
    await callback.answer(f"Обрано {button.widget_id}")


async def on_source_link_entered(
    message: Message, widget: TextInput, manager: DialogManager, data: str
):
    if not validate_link(data, manager.dialog_data["selected_source_type"]):
        await message.answer("❌ Невірний формат посилання для цього типу джерела!")
        return

    source = {
        "type": manager.dialog_data["selected_source_type"],
        "link": data,
    }

    if "sources" not in manager.dialog_data:
        manager.dialog_data["sources"] = []

    manager.dialog_data["sources"].append(source)
    manager.dialog_data["source_link"] = data

    await manager.switch_to(CreateFlowMenu.source_confirmation)


async def add_more_sources(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CreateFlowMenu.select_source)
    await callback.answer("Додаємо ще одне джерело")


async def show_my_sources(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await callback.answer("Список ваших джерел...")


def validate_link(link: str, source_type: str) -> bool:
    patterns = {
        "instagram": r"(https?:\/\/)?(www\.)?instagram\.com\/[A-Za-z0-9_\.]+",
        "facebook": r"(https?:\/\/)?(www\.)?facebook\.com\/[A-Za-z0-9_\.]+",
        "web": r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
        "telegram": r"(https?:\/\/)?(www\.)?t\.me\/(\+)?[A-Za-z0-9_\.]+",
    }
    import re

    return bool(re.fullmatch(patterns.get(source_type.lower(), ""), link))


# ==================FREQUENCY======================


async def on_once_a_day(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["selected_frequency"] = "daily"
    await callback.answer("Раз на день")
    await manager.switch_to(CreateFlowMenu.select_words_limit)


async def on_once_a_12(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["selected_frequency"] = "12h"
    await callback.answer("Раз на 12 годин")
    await manager.switch_to(CreateFlowMenu.select_words_limit)


async def on_once_an_hour(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["selected_frequency"] = "hourly"
    await callback.answer("Раз на годину")
    await manager.switch_to(CreateFlowMenu.select_words_limit)


# ==================WORDS LIMIT======================


async def on_to_100(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["selected_words_limit"] = "to_100"
    await callback.answer("До 100")
    await manager.switch_to(CreateFlowMenu.title_highlight_confirm)


async def on_to_300(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["selected_words_limit"] = "to_300"
    await callback.answer("До 300")
    await manager.switch_to(CreateFlowMenu.title_highlight_confirm)


async def on_to_1000(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["selected_words_limit"] = "to_1000"
    await callback.answer("До 1000")
    await manager.switch_to(CreateFlowMenu.title_highlight_confirm)


# ==================TITLE======================


async def confirm_title_highlight(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["title_highlight"] = True
    await manager.switch_to(CreateFlowMenu.flow_volume_settings)
    await callback.answer("Заголовок буде виділено")


async def reject_title_highlight(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["title_highlight"] = False
    await manager.switch_to(CreateFlowMenu.flow_volume_settings)
    await callback.answer("Заголовок не буде виділено")


# ==================AD TIME======================


async def handle_time_input(message: Message, widget, manager: DialogManager):
    if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", message.text):
        await message.answer(
            "❌ Невірний формат часу. Введіть у форматі hh:mm (наприклад, 15:20)"
        )
        return

    manager.dialog_data["ad_time"] = message.text

    await manager.switch_to(CreateFlowMenu.flow_volume_settings)
    await message.answer(f"✅ Час рекламного топу оновлено: {message.text}")


async def reset_ad_time(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["ad_time"] = None
    await callback.answer("Час рекламного топу скинуто")
    await manager.show()


# ==================POSTS VOLUME======================


async def on_volume_selected(
    callback: CallbackQuery, widget, manager: DialogManager, item_id: str
):
    manager.dialog_data["flow_volume"] = int(item_id)
    await manager.switch_to(CreateFlowMenu.signature_settings)
    await callback.answer(f"Встановлено зберігання {item_id} постів")


async def open_custom_volume_input(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CreateFlowMenu.custom_volume_input)
    await callback.answer("Введіть число від 1 до 50")


async def handle_custom_volume_input(message: Message, widget, manager: DialogManager):
    try:
        volume = int(message.text)
        if 1 <= volume <= 50:
            manager.dialog_data["flow_volume"] = volume
            await manager.switch_to(CreateFlowMenu.signature_settings)
            await message.answer(f"✅ Встановлено: {volume} постів")
        else:
            await message.answer("❌ Число має бути від 1 до 50")
    except ValueError:
        await message.answer("❌ Введіть коректне число")


# ==================SIGNATURE======================


# async def handle_signature_input(message: Message, widget, manager: DialogManager):
#     try:
#         manager.dialog_data["signature_raw"] = message.html_text
#         manager.dialog_data["signature"] = message.text

#         flow = await create_new_flow(manager)

#         await manager.switch_to(CreateFlowMenu.confirmation)

#     except Exception as e:
#         logger.error(f"Signature input error: {e}")
#         await message.answer("❌ Помилка збереження підпису")
#         await manager.switch_to(CreateFlowMenu.select_theme)


async def handle_signature_input(message: Message, widget, manager: DialogManager):
    try:
        new_signature = parse_entities_to_html(message)

        if len(new_signature) > 200:
            await message.answer(
                "⚠️ <b>Підпис занадто довгий</b>\nМаксимум 200 символів",
                parse_mode=ParseMode.HTML,
            )
            return

        await message.answer(
            f"✅ <b>Підпис:</b>\n{new_signature}", parse_mode=ParseMode.HTML
        )
        manager.dialog_data["signature"] = new_signature

        flow = await create_new_flow(manager)

        await manager.switch_to(CreateFlowMenu.confirmation)

    except Exception as e:
        logging.error(f"Signature processing error: {str(e)}")
        await message.answer(
            "⚠️ <b>Помилка!</b> Не вдалось обробити підпис", parse_mode=ParseMode.HTML
        )


async def skip_signature(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    try:
        manager.dialog_data["signature"] = None

        flow = await create_new_flow(manager)

        await manager.switch_to(CreateFlowMenu.confirmation)

    except ChannelNotFoundError:
        await callback.answer("❌ Канал не знайдено")
        await manager.switch_to(CreateFlowMenu.select_theme)
    except Exception as e:
        logger.error(f"Flow creation error: {e}")
        await callback.answer("❌ Помилка створення Flow")
        await manager.switch_to(CreateFlowMenu.select_theme)


# ==================CONFIRMATION======================


async def create_new_flow(manager: DialogManager):
    flow_data = manager.dialog_data

    channel = flow_data.get("selected_channel") or manager.start_data.get(
        "selected_channel"
    )
    if not channel:
        raise ValueError("Channel ID not found")

    channel_id = channel.channel_id
    channel_name = channel.name

    flow_service = Container.flow_service()

    new_flow = await flow_service.create_flow(
        channel_id=int(channel_id),
        name=channel_name,
        theme=flow_data.get("channel_theme", "Загальна"),
        sources=flow_data.get("sources", []),
        content_length=ContentLength(flow_data.get("selected_words_limit", "to_1000")),
        use_emojis=flow_data.get("use_emojis", False),
        use_premium_emojis=flow_data.get("use_premium_emojis", False),
        title_highlight=flow_data.get("title_highlight", False),
        cta=flow_data.get("cta", False),
        frequency=GenerationFrequency(flow_data.get("selected_frequency", "daily")),
        signature=flow_data.get("signature", ""),
        flow_volume=flow_data.get("flow_volume", 5),
        ad_time=flow_data.get("ad_time"),
    )
    manager.dialog_data["created_flow"] = {
        "flow_id": new_flow.id,
        "flow_name": new_flow.name,
    }

    return new_flow


async def start_generation_process(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    try:
        flow_data = manager.dialog_data.get("created_flow", {})
        channel = manager.dialog_data.get("selected_channel")

        flow_id = flow_data.get("flow_id")

        if not flow_id:
            raise ValueError("Flow ID not found in dialog data")

        flow_service = Container.flow_service()
        flow = await flow_service.get_flow_by_id(flow_id)

        logger.info(f"Starting generation for Flow ID: {flow_id}")

        await callback.answer("🔄 Запускаю генерацію...")

        bot = manager.middleware_data["bot"]
        status_msg = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"⚡ Генерація для флоу *{flow.name}*...",
            parse_mode="Markdown",
        )

        process = subprocess.Popen(
            [
                "python",
                "generator_worker.py",
                str(flow.id),
                str(callback.message.chat.id),
                str(status_msg.message_id),
                bot.token,
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,
            bufsize=1,
        )

        asyncio.create_task(
            show_generated_posts(
                process=process,
                flow_id=flow.id,
                chat_id=callback.message.chat.id,
                status_msg_id=status_msg.message_id,
                bot=bot,
                flow=flow,
                channel=channel,
            )
        )

    except Exception as e:
        logging.error(f"Помилка запуску генерації: {str(e)}")
        await callback.message.answer(f"❌ Помилка: {str(e)}", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        await callback.answer("❌ Помилка запуску генерації")
