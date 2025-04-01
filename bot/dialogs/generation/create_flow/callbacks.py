import re
import logging
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import TextInput

from .states import CreateFlowMenu
from bot.containers import Container

logger = logging.getLogger(__name__)

from dialogs.generation.states import GenerationMenu

async def to_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(GenerationMenu.main, mode=StartMode.RESET_STACK)

async def to_select_frequency(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(CreateFlowMenu.select_frequency)

# ==================SOURCE======================

async def on_source_type_selected(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["selected_source_type"] = button.widget_id
    manager.dialog_data["selected_source_name"] = button.text
    
    await manager.switch_to(CreateFlowMenu.add_source_link)
    await callback.answer(f"Обрано {button.widget_id}")

async def on_source_link_entered(message: Message, widget: TextInput, manager: DialogManager, data: str):
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

async def add_more_sources(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(CreateFlowMenu.select_source)
    await callback.answer("Додаємо ще одне джерело")

async def continue_to_next_step(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(CreateFlowMenu.next_step)
    await callback.answer("Продовжуємо налаштування флоу")

async def show_my_sources(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Список ваших джерел...")

def validate_link(link: str, source_type: str) -> bool:
    patterns = {
        "instagram": r"(https?:\/\/)?(www\.)?instagram\.com\/[A-Za-z0-9_\.]+",
        "facebook": r"(https?:\/\/)?(www\.)?facebook\.com\/[A-Za-z0-9_\.]+",
        "web": r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
        "telegram": r"(https?:\/\/)?(www\.)?t\.me\/[A-Za-z0-9_\.]+"
    }
    import re
    return bool(re.match(patterns.get(source_type.lower(), ""), link))

# ==================FREQUENCY======================

async def on_once_a_day(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_frequency'] = 'once_a_day'
    await callback.answer("Раз на день")
    await manager.switch_to(CreateFlowMenu.select_words_limit)

async def on_once_a_12(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_frequency'] = 'once_a_12'
    await callback.answer("Раз на 12 годин")
    await manager.switch_to(CreateFlowMenu.select_words_limit)

async def on_once_an_hour(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_frequency'] = 'once_an_hour'
    await callback.answer("Раз на годину")
    await manager.switch_to(CreateFlowMenu.select_words_limit)

# ==================WORDS LIMIT======================

async def on_to_100(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_words_limit'] = 'to_100'
    await callback.answer("До 100")
    await manager.switch_to(CreateFlowMenu.title_highlight_confirm)

async def on_to_300(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_words_limit'] = 'to_300'
    await callback.answer("До 300")
    await manager.switch_to(CreateFlowMenu.title_highlight_confirm)

async def on_to_1000(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data['selected_words_limit'] = 'to_1000'
    await callback.answer("До 1000")
    await manager.switch_to(CreateFlowMenu.title_highlight_confirm)


# ==================TITLE======================

async def confirm_title_highlight(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["title_highlight"] = True
    await manager.switch_to(CreateFlowMenu.ad_time_settings)
    await callback.answer("Заголовок буде виділено")

async def reject_title_highlight(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["title_highlight"] = False
    await manager.switch_to(CreateFlowMenu.ad_time_settings)
    await callback.answer("Заголовок не буде виділено")


# ==================AD TIME======================


async def handle_time_input(message: Message, widget, manager: DialogManager):
    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', message.text):
        await message.answer("❌ Невірний формат часу. Введіть у форматі hh:mm (наприклад, 15:20)")
        return
    
    manager.dialog_data["ad_time"] = message.text

    await manager.switch_to(CreateFlowMenu.flow_volume_settings)
    await message.answer(f"✅ Час рекламного топу оновлено: {message.text}")

async def reset_ad_time(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["ad_time"] = None
    await callback.answer("Час рекламного топу скинуто")
    await manager.show()


# ==================POSTS VOLUME======================
    

async def on_volume_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["flow_volume"] = int(item_id)
    await manager.switch_to(CreateFlowMenu.signature_settings)
    await callback.answer(f"Встановлено зберігання {item_id} постів")

async def open_custom_volume_input(callback: CallbackQuery, button: Button, manager: DialogManager):
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


async def handle_signature_input(message: Message, widget, manager: DialogManager):
    manager.dialog_data["signature"] = message.text
    logging.info(manager.dialog_data)
    await manager.switch_to(CreateFlowMenu.confirmation)
    await message.answer(f"✅ Підпис оновлено:\n{message.text}")

async def skip_signature(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["signature"] = None
    logging.info(manager.dialog_data)
    await callback.answer("Підпис видалено")
    await manager.switch_to(CreateFlowMenu.confirmation)


# ==================CONFIRMATION======================


async def show_my_flows(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await manager.start(MyFlowsMenu.list)
    await callback.answer("Список ваших Flow")

async def start_generation_process(callback: CallbackQuery, button: Button, manager: DialogManager):
    try:
        flow_data = manager.dialog_data.get("created_flow", {})
        flow_id = flow_data.get("id")
        
        if not flow_id:
            raise ValueError("Flow ID not found in dialog data")
        
        flow_service = Container.flow_service()
        flow = await flow_service.get_flow_by_id(flow_id)
        
        logger.info(f"Starting generation for Flow ID: {flow_id}")
        
        await callback.answer(f"🔁 Генерація для '{flow.name}' запущена!")
        await manager.switch_to(GenerationMenu.status)
        
    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        await callback.answer("❌ Помилка запуску генерації")