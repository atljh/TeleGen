import os
import sys
import asyncio
import logging

from bot.containers import Container
from bot.utils.notifications import send_telegram_notification

async def generate_flow(
    flow_id: int,
    chat_id: int,
) -> None:
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        flow_service = Container.flow_service()
        flow = await flow_service.get_flow_by_id(flow_id)
        
        if not flow:
            await send_telegram_notification(
                bot_token,
                chat_id,
                f"❌ Флоу з ID {flow_id} не знайдено"
            )
            return

        userbot_service = Container.enhanced_userbot_service()
        posts = await userbot_service.get_last_posts(flow)
        
        await send_telegram_notification(
            bot_token,
            chat_id,
            f"✅ Генерація для флоу *{flow.name}* завершена успішно!\n"
            f"• Створено постів: {len(posts)}\n"
            f"• Обсяг флоу: {flow.flow_volume}",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Помилка генерації: {str(e)}", exc_info=True)
        await send_telegram_notification(
            bot_token,
            chat_id,
            f"❌ Критична помилка під час генерації флоу {flow_id}:\n"
            f"_{str(e)}_",
            parse_mode="Markdown"
        )
        raise

if __name__ == "__main__":
    flow_id = int(sys.argv[1])
    chat_id = int(sys.argv[2])
    asyncio.run(generate_flow(flow_id, chat_id))