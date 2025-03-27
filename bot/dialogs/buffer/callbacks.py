import logging
import datetime
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row, Back
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu 
from bot.containers import Container

logger = logging.getLogger(__name__)


async def publish_now(callback: CallbackQuery, button: Button, manager: DialogManager):
    try:
        bot: Bot = manager.middleware_data["bot"]
        channel_service = Container.channel_service()
        
        selected_channel = manager.dialog_data.get("selected_channel")
        if not selected_channel:
            await callback.answer("Канал не вибрано!")
            return
        
        test_post = (
            "📢 <b>Тестова публікація</b>\n\n"
            "Це тестовий пост для перевірки функціоналу.\n\n"
            "🕒 Час публікації: " + datetime.now().strftime("%H:%M %d.%m.%Y")
        )
        
        await bot.send_message(
            chat_id=selected_channel.channel_id,
            text=test_post,
            parse_mode=ParseMode.HTML
        )
        
        await channel_service.log_publication(
            user_id=callback.from_user.id,
            channel_id=selected_channel.id,
            content=test_post
        )
        
        await callback.answer("✅ Тестовий пост успішно опубліковано!")
        await callback.message.answer(f"📢 Тестова публікація відправлена в канал {selected_channel.name}")
        
    except Exception as e:
        logger.error(f"Помилка публікації: {e}")
        await callback.answer("❌ Помилка при публікації!")

async def schedule_publish(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("📅 Публікацію заплановано!")

async def edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("✏️ Відкрито редактор публікації!")

async def delete_draft(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("🗑 Чернетку видалено!")

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
