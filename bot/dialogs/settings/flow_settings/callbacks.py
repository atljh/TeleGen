import logging
from aiogram import F
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
    await m.switch_to(FlowSettingsMenu.add_source)

async def to_select_source_to_edit(c: CallbackQuery, b: Button, m: DialogManager):
    data = await get_sources_data(m)
    if not data["sources"]:
        await c.answer("Немає джерел для редагування")
        return
    await m.switch_to(FlowSettingsMenu.select_source_to_edit)

async def to_select_source_to_delete(c: CallbackQuery, b: Button, m: DialogManager):
    data = await get_sources_data(m)
    if not data["sources"]:
        await c.answer("Немає джерел для видалення")
        return
    await m.switch_to(FlowSettingsMenu.select_source_to_delete)

async def back_to_settings(c: CallbackQuery, b: Button, m: DialogManager):
    await m.done()


async def on_source_type_selected(c: CallbackQuery, b: Button, m: DialogManager):
    source_type = b.widget_id.replace("source_", "")
    m.dialog_data["new_source_type"] = source_type
    await m.switch_to(FlowSettingsMenu.add_source_link)

async def on_source_link_entered(message: Message, i, m: DialogManager, link: str):
    flow_service = Container.flow_service()
    flow_id = m.dialog_data["channel_flow"].id
    
    new_source = {
        "type": m.dialog_data["new_source_type"],
        "link": link
    }
    
    await flow_service.add_source_to_flow(flow_id, new_source)
    await m.answer(f"Джерело {new_source['type']} додано!")
    await m.switch_to(FlowSettingsMenu.select_action)

async def on_source_selected_for_edit(c: CallbackQuery, s, m: DialogManager, item_id: str):
    m.dialog_data["editing_source_id"] = item_id
    await m.switch_to(FlowSettingsMenu.edit_source)

async def on_edit_link_clicked(c: CallbackQuery, b: Button, m: DialogManager):
    await m.switch_to(FlowSettingsMenu.edit_source_link)

async def on_source_selected_for_delete(c: CallbackQuery, s, m: DialogManager, item_id: str):
    flow_service = Container.flow_service()
    flow_id = m.dialog_data["channel_flow"].id
    
    await flow_service.remove_source_from_flow(flow_id, item_id)
    await c.answer("Джерело видалено!")
    await m.switch_to(FlowSettingsMenu.select_action)

async def to_edit_link(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.edit_link)

async def to_edit_type(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowSettingsMenu.edit_source_type)