import logging
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button, Row, Column, Back, Calendar
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu 
from .states import BufferMenu
from bot.containers import Container

logger = logging.getLogger(__name__)


async def publish_now(callback: CallbackQuery, button: Button, manager: DialogManager):
    try:
        bot: Bot = manager.middleware_data["bot"]
        channel_service = Container.channel_service()
        channels = await channel_service.get_user_channels(callback.from_user.id)
        logger.info(channels)
    
        # selected_channel = manager.dialog_data.get("selected_channel")
        # if not selected_channel:
        #     await callback.answer("Канал не вибрано!")
        #     return
        for selected_channel in channels:
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
            
            # await channel_service.log_publication(
            #     user_id=callback.from_user.id,
            #     channel_id=selected_channel.id,
            #     content=test_post
            # )
            
            await callback.answer("✅ Тестовий пост успішно опубліковано!")
            await callback.message.answer(f"📢 Тестова публікація відправлена в канал {selected_channel.name}")
            
    except Exception as e:
        logger.error(f"Помилка публікації: {e}")
        await callback.answer("❌ Помилка при публікації!")

async def on_text_edited(message: Message, widget: MessageInput, manager: DialogManager):
    manager.dialog_data['post_text'] = message.html_text
    await manager.switch_to(BufferMenu.edit_media)

async def on_media_edited(message: Message, widget: MessageInput, manager: DialogManager):
    if message.photo:
        manager.dialog_data['media'] = message.photo[-1].file_id
    elif message.video:
        manager.dialog_data['media'] = message.video.file_id
    await manager.switch_to(BufferMenu.set_schedule)

async def on_calendar_selected(callback: CallbackQuery, widget: Calendar, 
                             manager: DialogManager, selected_date: datetime):
    manager.dialog_data['publish_time'] = selected_date
    await manager.switch_to(BufferMenu.preview)

async def publish_immediately(callback: CallbackQuery, button: Button, manager: DialogManager):
    await process_publication(callback, manager, immediate=True)

async def schedule_publication(callback: CallbackQuery, button: Button, manager: DialogManager):
    await process_publication(callback, manager, immediate=False)

async def process_publication(callback: CallbackQuery, manager: DialogManager, immediate: bool):
    bot = manager.middleware_data['bot']
    post_data = manager.dialog_data
    
    try:
        if immediate:
            await send_post(bot, post_data)
            await callback.answer("✅ Пост опубліковано!")
        else:
            publish_time = post_data.get('publish_time', datetime.now() + timedelta(hours=1))
            await schedule_post(bot, post_data, publish_time)
            await callback.answer(f"📅 Пост заплановано на {publish_time.strftime('%d.%m.%Y %H:%M')}")
        
        await manager.done()
    except Exception as e:
        await callback.answer(f"❌ Помилка: {str(e)}")

async def send_post(bot: Bot, post_data: dict):
    if 'media' in post_data:
        await bot.send_photo(
            chat_id=post_data['channel_id'],
            photo=post_data['media'],
            caption=post_data['post_text'],
            parse_mode=ParseMode.HTML
        )
    else:
        await bot.send_message(
            chat_id=post_data['channel_id'],
            text=post_data['post_text'],
            parse_mode=ParseMode.HTML
        )

async def schedule_post(bot: Bot, post_data: dict, publish_time: datetime):
    pass