from aiogram import Bot


async def is_valid_channel(bot: Bot, channel_id: str) -> bool:
    try:
        chat = await bot.get_chat(channel_id)
        return chat.type in ["channel", "supergroup"]
    except Exception:
        return False
    
def is_valid_link(link: str) -> bool:
    return link.startswith(('http://', 'https://'))