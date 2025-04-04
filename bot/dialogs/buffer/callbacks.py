import logging
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button, Row, Column, Back, Calendar
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog import DialogManager, StartMode

from .states import BufferMenu
from .edit_buffer import EditPostMenu
from bot.containers import Container

logger = logging.getLogger(__name__)


async def publish_now(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    try:
        bot: Bot = manager.middleware_data["bot"]
        channel_service = Container.channel_service()
        
        channels = await channel_service.get_user_channels(callback.from_user.id)
        
        if not channels:
            await callback.answer("❗ У вас немає підключених каналів!")
            return
            
        for channel in channels:
            try:
                await process_publication(callback, manager, immediate=True, channel_id=channel.channel_id)
            except Exception as channel_error:
                logger.error(f"Помилка публікації в канал {channel.name}: {channel_error}")
                await callback.message.answer(
                    f"❌ Не вдалося опублікувати в каналі {channel.name}\n"
                    f"Перевірте права бота та налаштування каналу"
                )
        
        await callback.answer("🔄 Публікація завершена")
        await manager.start(BufferMenu.preview)

    except Exception as e:
        logger.error(f"Критична помилка публікації: {e}")
        await callback.answer("❌ Сталася критична помилка при публікації!")


async def on_text_edited(message: Message, widget: MessageInput, manager: DialogManager):
    await manager.start(EditPostMenu.edit_options)

async def process_publication(callback: CallbackQuery, manager: DialogManager, immediate: bool, channel_id: int):
    bot = manager.middleware_data['bot']
    post_data = manager.dialog_data
    
    try:
        if immediate:
            await send_post(bot, post_data, channel_id)
            await callback.answer("✅ Пост опубліковано!")
        else:
            publish_time = post_data.get('publish_time', datetime.now() + timedelta(hours=1))
            await schedule_post(bot, post_data, publish_time)
            await callback.answer(f"📅 Пост заплановано на {publish_time.strftime('%d.%m.%Y %H:%M')}")
        
        await manager.done()
    except Exception as e:
        await callback.answer(f"❌ Помилка: {str(e)}")

async def send_post(bot: Bot, post_data: dict, channel_id: int):
    if 'media' in post_data:
        await bot.send_photo(
            chat_id=channel_id,
            photo=post_data['media'],
            caption=post_data['post_text'],
            parse_mode=ParseMode.HTML
        )
    else:
        await bot.send_message(
            chat_id=channel_id,
            text=post_data['post_text'],
            parse_mode=ParseMode.HTML
        )


async def open_calendar(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    await dialog_manager.switch_to(BufferMenu.set_schedule)

async def schedule_post(callback: CallbackQuery, widget, manager: DialogManager, selected_date):
    await callback.answer(f"Заплановано на {selected_date.strftime('%d.%m.%Y')}")
    await manager.switch_to(BufferMenu.preview)
