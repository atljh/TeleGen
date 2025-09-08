from aiogram import Bot
from typing import Optional
import logging


async def check_bot_permissions(bot: Bot, chat_id: str) -> Optional[dict]:
    try:
        chat_member = await bot.get_chat_member(chat_id, bot.id)
        return {
            "can_post_messages": chat_member.can_post_messages,
            "can_edit_messages": chat_member.can_edit_messages,
            "can_delete_messages": chat_member.can_delete_messages,
            "can_manage_chat": chat_member.can_manage_chat,
        }
    except Exception as e:
        logging.error(f"Помилка перевірки прав: {e}")
        return None
