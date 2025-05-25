from datetime import datetime
import logging
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, Window, Dialog
from aiogram_dialog.widgets.kbd import Button

from bot.containers import Container
from bot.dialogs.settings.flow_settings.getters import get_sources_data

from .states import FlowSettingsMenu
from dialogs.settings.states import SettingsMenu

logger = logging.getLogger(__name__)

# ================== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ФЛОУ ==================

async def start_flow_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    flow_service = Container.flow_service()

    start_data = manager.start_data or {}
    dialog_data = manager.dialog_data or {}
    selected_channel = (
        start_data.get("selected_channel", False)
        or dialog_data.get('selected_channel, False')
    )
    logging.info(f'----{selected_channel}')
    channel_flow = await flow_service.get_flow_by_channel_id(selected_channel.id)
    if not channel_flow:
        await callback.answer(f"У канала {selected_channel.name} поки немає Флоу")
        return
    await manager.start(
        FlowSettingsMenu.flow_settings,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow
        },
        mode=StartMode.RESET_STACK 
    )

async def open_flow_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.flow_settings)

async def open_main_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    start_data = manager.start_data or {}
    dialog_data = manager.dialog_data or {}
    selected_channel = (
        start_data.get("selected_channel", False)
        or dialog_data.get('selected_channel, False')
    )
    channel_flow = (
        start_data.get("channel_flow", False)
        or dialog_data.get("channel_flow", False)
    )
    await manager.start(
        SettingsMenu.channel_settings,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow
        },
        mode=StartMode.RESET_STACK 
    )
    return

async def back_to_settings(callback: CallbackQuery, b: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get('channel_flow')
    if not channel_flow:
        await callback.answer(f"У канала {selected_channel.name} поки немає Флоу")
        return
    await manager.start(
        FlowSettingsMenu.flow_settings,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow
        },
        mode=StartMode.RESET_STACK 
    )

# ================== ОСНОВНЫЕ ОБРАБОТЧИКИ ФЛОУ ==================

async def set_generation_frequency(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.generation_frequency)

async def character_limit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.character_limit)

async def toggle_title_highlight(callback: CallbackQuery, button: Button, manager: DialogManager):

    if "channel_flow" not in manager.dialog_data:
        manager.dialog_data["channel_flow"] = manager.start_data["channel_flow"]
    
    current = manager.dialog_data["channel_flow"].title_highlight

    manager.dialog_data["channel_flow"].title_highlight = not current
    
    flow_service = Container.flow_service()
    await flow_service.update_flow(
        flow_id=manager.dialog_data["channel_flow"].id,
        title_highlight=not current
    )

    await callback.answer(f"Виділення заголовку {'увімкнено' if not current else 'вимкнено'}")

async def configure_ad_block(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.ad_block_settings)

async def set_posts_in_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.posts_in_flow)

async def open_source_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.source_settings)


# ================== ОБРАБОТЧИКИ ПОД-НАСТРОЕК ==================

async def set_frequency(
    callback: CallbackQuery, 
    button: Button, 
    manager: DialogManager
):
    freq_map = {
        "freq_1h": "hourly",
        "freq_12h": "12h",
        "freq_24h": "daily"
    }
    
    try:
        if button.widget_id not in freq_map:
            await callback.answer("Невідома частота генерації")
            return

        new_frequency = freq_map[button.widget_id]
        
        if "channel_flow" not in manager.dialog_data:
            manager.dialog_data["channel_flow"] = manager.start_data["channel_flow"]
        
        manager.dialog_data["channel_flow"].frequency = new_frequency
        
        flow_service = Container.flow_service()
        await flow_service.update_flow(
            flow_id=manager.dialog_data["channel_flow"].id,
            frequency=new_frequency
        )

        await callback.answer(f"✅ Частоту оновлено")
        await manager.back()
        await manager.show()
        
    except Exception as e:
        await callback.answer("❌ Помилка при оновленні частоти")
        logger.error(f"Error updating frequency: {e}")

async def set_character_limit(callback: CallbackQuery, button: Button, manager: DialogManager):
    
    limit_map = {
        "limit_100": "to_100",
        "limit_300": "to_300",
        "limit_1000": "to_1000"
    }
    if button.widget_id not in limit_map:
        await callback.answer("Невідомий лiмiт символiв")
        return
    
    new_limit = limit_map[button.widget_id]

    if "channel_flow" not in manager.dialog_data:
        manager.dialog_data["channel_flow"] = manager.start_data["channel_flow"]

    manager.dialog_data["channel_flow"].content_length = new_limit

    flow_service = Container.flow_service()
    await flow_service.update_flow(
        flow_id=manager.dialog_data["channel_flow"].id,
        content_length=new_limit
    )

    manager.dialog_data["words_limit"] = new_limit

    await callback.answer(f"✅ Лiмiт оновлено")
    
    await manager.switch_to(FlowSettingsMenu.flow_settings)

async def toggle_ad_block(callback: CallbackQuery, button: Button, manager: DialogManager):
    ad_enabled = button.widget_id == "enable_ads"
    manager.dialog_data["ad_enabled"] = ad_enabled
    await callback.answer(f"Рекламний блок {'увімкнено' if ad_enabled else 'вимкнено'}")
    await manager.switch_to(FlowSettingsMenu.flow_settings)

async def set_flow_volume(callback: CallbackQuery, button: Button, manager: DialogManager):
    volume_map = {
        'volume_5': 5,
        'volume_10': 10,
        'volume_20': 20
    }
    if button.widget_id not in volume_map:
        await callback.answer("Невідома кількість постів у флоу")
        return
    
    new_volume= volume_map[button.widget_id]

    if "channel_flow" not in manager.dialog_data:
        manager.dialog_data["channel_flow"] = manager.start_data["channel_flow"]

    manager.dialog_data["channel_flow"].flow_volume = new_volume

    flow_service = Container.flow_service()
    await flow_service.update_flow(
        flow_id=manager.dialog_data["channel_flow"].id,
        flow_volume=new_volume
    )
    await callback.answer(f"✅ Лiмiт оновлено")

    await manager.switch_to(FlowSettingsMenu.flow_settings)



async def to_add_source(c: CallbackQuery, b: Button, m: DialogManager):
    await m.switch_to(FlowSettingsMenu.add_source_type)

async def to_select_source_to_edit(c: CallbackQuery, b: Button, m: DialogManager):
    data = await get_sources_data(m)
    if not data["sources"]:
        await c.answer("Немає джерел для редагування")
        return
    await m.switch_to(FlowSettingsMenu.edit_select_source)

async def to_select_source_to_delete(c: CallbackQuery, b: Button, m: DialogManager):
    data = await get_sources_data(m)
    if not data["sources"]:
        await c.answer("Немає джерел для видалення")
        return
    await m.switch_to(FlowSettingsMenu.select_source_to_delete)


async def on_source_type_selected(callback: CallbackQuery, button: Button, manager: DialogManager):
    type_mapping = {
        "source_instagram": "instagram",
        "source_web": "web",
        "source_telegram": "telegram"
    }
    manager.dialog_data["new_source_type"] = type_mapping[button.widget_id]
    await manager.switch_to(FlowSettingsMenu.add_source_link)

async def on_source_link_entered(message: Message, widget, manager: DialogManager, link: str):
    try:
        flow = manager.dialog_data.get("channel_flow", manager.start_data["channel_flow"])
        source_type = manager.dialog_data["new_source_type"]
        
        new_source = {
            "type": source_type,
            "link": link,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        if not hasattr(flow, "sources"):
            flow.sources = []
        
        if any(src['link'] == link for src in flow.sources):
            await message.answer("⚠️ Це джерело вже додано!")
            return
            
        flow.sources.append(new_source)
        
        flow_service = Container.flow_service()
        await flow_service.update_flow(
            flow_id=flow.id,
            sources=flow.sources
        )
        
        await message.answer(f"✅ Джерело {source_type} успішно додано!")
        await manager.switch_to(FlowSettingsMenu.source_settings)
        
    except Exception as e:
        logger.error(f"Error adding source: {e}")
        await message.answer("❌ Помилка при додаванні джерела")
        await manager.back()

async def on_source_selected_for_edit(
    callback: CallbackQuery, 
    select, 
    manager: DialogManager, 
    item_id: str
):
    try:
        source_idx = int(item_id)
        manager.dialog_data["editing_source_idx"] = source_idx
        await manager.switch_to(FlowSettingsMenu.edit_source)
    except Exception as e:
        logger.error(f"Помилка вибору джерела: {e}")
        await callback.answer("❌ Помилка при виборі джерела")

async def on_edit_link_clicked(c: CallbackQuery, b: Button, m: DialogManager):
    await m.switch_to(FlowSettingsMenu.edit_source_link)

async def on_new_type_selected(
    callback: CallbackQuery, 
    button: Button, 
    manager: DialogManager
):
    try:
        flow = manager.dialog_data.get("channel_flow", manager.start_data["channel_flow"])
        if not flow:
            raise ValueError("Не знайдено дані флоу")
        
        source_idx = manager.dialog_data.get("editing_source_idx")
        if source_idx is None:
            raise ValueError("Не вказано індекс джерела")
        
        type_mapping = {
            "source_web": "web",
            "source_instagram": "instagram",
            "source_telegram": "telegram",
        }
        
        new_type = type_mapping.get(button.widget_id)
        if not new_type:
            raise ValueError(f"Невідомий тип джерела: {button.widget_id}")
        
        flow.sources[source_idx]["type"] = new_type
        flow.sources[source_idx]["updated_at"] = datetime.now().isoformat()
        
        flow_service = Container.flow_service()
        await flow_service.update_flow(
            flow_id=flow.id,
            sources=flow.sources
        )
        
        await callback.answer(
            f"✅ Тип змінено на: {new_type}",
            show_alert=True
        )
        
        await manager.switch_to(
            FlowSettingsMenu.source_settings
        )
        
    except ValueError as e:
        error_msg = f"Помилка валідації: {str(e)}"
        logger.warning(error_msg)
        await callback.answer(error_msg, show_alert=True)
        await manager.back()
        
    except IndexError:
        error_msg = "Джерело не знайдено (невірний індекс)"
        logger.error(error_msg)
        await callback.answer(error_msg, show_alert=True)
        await manager.done()
        
    except Exception as e:
        error_msg = "Критична помилка при зміні типу"
        logger.critical(f"{error_msg}: {str(e)}", exc_info=True)
        await callback.answer(error_msg, show_alert=True)
        await manager.done()

async def validate_url(message: Message):
    return message.startswith(('http://', 'https://'))

async def on_source_new_link_entered(
    message: Message, 
    widget, 
    manager: DialogManager, 
    new_link: str
):
    try:
        if not manager.has_context():
            await message.answer("🚫 Спробуйте заново")
            return

        flow = manager.dialog_data.get("channel_flow", manager.start_data["channel_flow"])

        if not flow:
            raise ValueError("Помилка при завантаженi флоу")

        source_idx = manager.dialog_data.get("editing_source_idx")
        if source_idx is None or not (0 <= source_idx < len(flow.sources)):
            raise ValueError("Помилка при отриманнi джерела")

        if not await validate_url(new_link):
            await message.answer("❌ Використовуйте http:// або https://")
            return

        if any(
            i != source_idx and src["link"] == new_link 
            for i, src in enumerate(flow.sources)
        ):
            await message.answer("⚠️ Це джерело вже додано!")
            return

        old_link = flow.sources[source_idx]["link"]
        flow.sources[source_idx]["link"] = new_link
        flow.sources[source_idx]["updated_at"] = datetime.now().isoformat()

        flow_service = Container.flow_service()
        updated_flow = await flow_service.update_flow(
            flow_id=flow.id,
            sources=flow.sources
        )

        await message.answer(
            f"✅ Джерело успішно змiнено!:\n\n"
            f"Було: <code>{old_link}</code>\n"
            f"Стало: <code>{new_link}</code>",
            parse_mode=ParseMode.HTML
        )

        await manager.switch_to(
            FlowSettingsMenu.source_settings
        )

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        await manager.back()

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        await message.answer("⛔ Произошла непредвиденная ошибка")
        await manager.done()

async def on_source_selected_for_delete(callback: CallbackQuery, select, manager: DialogManager, item_id: str):
    manager.dialog_data["source_to_delete"] = item_id
    
    await manager.switch_to(FlowSettingsMenu.confirm_delete_source)



async def confirm_delete_source(callback: CallbackQuery, button: Button, manager: DialogManager):
    flow = manager.dialog_data.get("channel_flow", manager.start_data["channel_flow"])
    item_id = manager.dialog_data["source_to_delete"]
    idx = int(item_id) - 1
    
    deleted_source = flow.sources[idx]
    flow.sources.pop(idx)
    
    flow_service = Container.flow_service()
    updated_flow = await flow_service.update_flow(
        flow_id=flow.id,
        sources=flow.sources
    )
    
    await callback.answer(
        f"✅ Джерело {deleted_source['type']} видалено!",
        show_alert=True
    )
    await manager.switch_to(FlowSettingsMenu.source_settings)

async def cancel_delete_source(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Видалення скасовано")
    await manager.switch_to(FlowSettingsMenu.select_source_to_delete)


async def to_edit_link(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.edit_source_link)

async def to_edit_type(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.edit_source_type)