import logging
from datetime import datetime
from typing import Any, Dict, List
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Back, Group, Cancel
from aiogram_dialog.widgets.kbd import Select, ScrollingGroup, Button, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.media import StaticMedia
from aiogram.enums import ParseMode 
from aiogram_dialog import DialogManager

from bot.containers import Container

from utils.buttons import (
    go_back_to_channel,
    go_back_to_main
)
from .states import FlowMenu
from .callbacks import (
    on_publish_now,
    on_schedule,
    on_edit,
    on_save_to_buffer,
    on_refresh_posts,
    on_post_select
)


async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}
    
    channel = (
        start_data.get("selected_channel") 
        or dialog_data.get("selected_channel")
    )
    flow = (
        start_data.get("channel_flow") 
        or dialog_data.get("channel_flow")
    )
    posts = []
    if flow:
        post_service = Container.post_service()
        raw_posts = await post_service.get_posts_by_flow_id(flow.id)
        
        for post in raw_posts:
            pub_time = post.publication_date.strftime("%d.%m.%Y %H:%M") if post.publication_date else "Без даты"
            posts.append({
                "id": str(post.id),
                "content_preview": (post.content[:100] + "...") if len(post.content) > 100 else post.content,
                "pub_time": pub_time,
                "status": "✅ Опубликован" if post.is_published else "📝 Черновик",
                "full_content": post.content
            })
    dialog_manager.dialog_data["posts"] = posts
    return {
        "channel_name": channel.name if channel else "Канал не выбран",
        "channel_id": getattr(channel, "channel_id", "N/A"),
        "channel_flow": flow.name if flow else "Нет флоу",
        "posts": posts,
        "posts_count": len(posts),
        "items": posts
    }

async def on_publish_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    post_service = Container.post_service()
    await post_service.publish_post(post_id)
    await callback.answer(f"Пост {post_id} опубликован!")
    await manager.show()

async def on_edit_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    post_id = manager.dialog_data.get("current_post_id")
    await callback.answer(f"Редактирование поста {post_id}")

async def on_next_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    posts = manager.dialog_data.get("posts", [])
    current_index = manager.dialog_data.get("post_index", 0)
    
    if current_index < len(posts) - 1:
        manager.dialog_data["post_index"] = current_index + 1
        manager.dialog_data["current_post_id"] = posts[current_index + 1]["id"]
    await manager.show()

async def on_prev_post(callback: CallbackQuery, button: Button, manager: DialogManager):
    posts = manager.dialog_data.get("posts", [])
    current_index = manager.dialog_data.get("post_index", 0)
    
    if current_index > 0:
        manager.dialog_data["post_index"] = current_index - 1
        manager.dialog_data["current_post_id"] = posts[current_index - 1]["id"]
    await manager.show()

async def get_current_post_data(dialog_manager: DialogManager, **kwargs):
    base_data = await selected_channel_getter(dialog_manager, **kwargs)
    posts = base_data.get("posts", [])
    current_index = dialog_manager.dialog_data.get("post_index", 0)
    
    if posts and 0 <= current_index < len(posts):
        current_post = posts[current_index]
        dialog_manager.dialog_data["current_post_id"] = current_post["id"]
        return {
            **base_data,
            "current_post": current_post,
            "post_number": current_index + 1,
            "has_next": current_index < len(posts) - 1,
            "has_prev": current_index > 0,
        }
    return base_data

def flow_dialog() -> Dialog:
    return Dialog(
        Window(
            Format("📌 Канал: {channel_name}\n"
                "📊 Флоу: {channel_flow}\n\n"
                "--- Пост {post_number}/{posts_count} ---\n\n"
                "📅 {current_post[pub_time]}\n"
                "🔄 {current_post[status]}\n\n"
                "{current_post[content_preview]}"),
            
            Group(
                Button(Const("⬅️ Назад"), id="prev_post", on_click=on_prev_post, when="has_prev"),
                Button(Const("➡️ Вперед"), id="next_post", on_click=on_next_post, when="has_next"),
                width=2
            ),
            
            Group(
                Button(Const("✅ Опубликовать"), id="publish_post", on_click=on_publish_post),
                Button(Const("✏️ Редактировать"), id="edit_post", on_click=on_edit_post),
                width=2
            ),
            
            Cancel(Const("🔙 Назад")),
            getter=get_current_post_data,
            state=FlowMenu.posts_list,  # Замените на ваше состояние
        ),
    )