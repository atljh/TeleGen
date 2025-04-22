import logging
from typing import Dict
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from bot.containers import Container
from bot.database.exceptions import InvalidOperationError

from .states import FlowMenu
from .getters import paging_getter, send_media_album


async def on_publish_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    dialog_data = await paging_getter(manager)
    start_data = manager.start_data or {}

    current_post = dialog_data["post"]
    post_id = current_post["id"]
    
    channel = start_data.get("selected_channel") or dialog_data.get("selected_channel")
    
    if not channel:
        await callback.answer("Канал не вибрано!")
        return
    
    post_service = Container.post_service()
    is_album = False
    
    try:
        updated_post = await post_service.publish_post(post_id, channel.channel_id)
        is_album = len(updated_post.images) > 1
        
        manager.dialog_data["post"] = {
            **current_post,
            "status": "✅ Опубліковано",
            "pub_time": updated_post.publication_date.strftime("%d.%m.%Y %H:%M"),
            "is_published": True
        }
        
        await callback.answer(f"Пост успiшно опублiковано в канал!")
        
    except InvalidOperationError as e:
        logging.error(e)
        await callback.answer(str(e))
    except Exception as e:
        logging.error(e)
        await callback.answer(f"Помилка: {str(e)}")
        logging.exception("Помилка при публікації посту")
    finally:
        await manager.show()

async def on_edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Редагування поста {post_id}")

async def on_schedule_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Запланувати публікацію поста {post_id}")

async def on_save_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    # post_service = Container.post_service()
    # await post_service.save_to_buffer(post_id)
    await callback.answer("Пост збережено в буфер!")


async def on_show_album(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    try:
        if not hasattr(dialog_manager, 'dialog_data'):
            await callback.answer("❌ Помилка: Відсутні дані диалогу")
            logging.error("Відсутній dialog_manager.dialog_data")
            return

        dialog_data = dialog_manager.dialog_data or {}
        
        logging.debug(f"Поточний стан dialog_data: {list(dialog_data.keys())}")
        
        if 'all_posts' not in dialog_data:
            await callback.answer("❌ Помилка: Відсутній ключ 'all_posts'")
            logging.error(f"Відсутній ключ 'all_posts'. Доступні ключі: {list(dialog_data.keys())}")
            return
            
        all_posts = dialog_data['all_posts']
        
        if not isinstance(all_posts, list):
            await callback.answer("❌ Помилка: Невірний формат даних постів")
            logging.error(f"all_posts має тип {type(all_posts)}, очікувався list")
            return
            
        if not all_posts:
            await callback.answer("❌ Помилка: Список постів порожній")
            logging.error("Список all_posts порожній, хоча не повинен бути")
            return
            
        first_post = all_posts[0]
        logging.debug(f"Приклад структури поста: {list(first_post.keys()) if isinstance(first_post, dict) else type(first_post)}")
        
        if 'current_page' not in dialog_data:
            await callback.answer("❌ Помилка: Відсутня поточна сторінка")
            logging.error("Відсутній ключ 'current_page'")
            return
            
        current_page = dialog_data['current_page']
        
        if current_page < 1 or current_page > len(all_posts):
            await callback.answer(f"❌ Помилка: Невірний номер сторінки {current_page}")
            logging.error(f"Невірний current_page: {current_page}, всього постів: {len(all_posts)}")
            return
            
        post_data = all_posts[current_page - 1]

        if not isinstance(post_data, dict):
            await callback.answer("❌ Помилка: Невірний формат поста")
            logging.error(f"Пост має тип {type(post_data)}, очікувався dict")
            return
            
        if 'images' not in post_data:
            await callback.answer("❌ Помилка: Відсутній ключ 'images'")
            logging.error(f"Відсутній ключ 'images' в пості. Доступні ключі: {list(post_data.keys())}")
            return
            
        images = post_data['images']
        
        if not isinstance(images, list):
            await callback.answer("❌ Помилка: Невірний формат зображень")
            logging.error(f"images має тип {type(images)}, очікувався list")
            return
            
        if len(images) < 2:
            await callback.answer(f"ℹ️ Для альбому потрібно ≥2 зображень (знайдено {len(images)})")
            return
            
        try:
            await send_media_album(dialog_manager, post_data)
        except Exception as e:
            logging.error(f"Помилка відправки альбому: {str(e)}", exc_info=True)
            await callback.answer("⚠️ Помилка відправки альбому")
            
    except Exception as e:
        logging.error(f"Критична помилка: {str(e)}", exc_info=True)
        await callback.answer("‼️ Критична помилка системи")
