import os
import sys
import asyncio
import logging
from typing import List

from bot.containers import Container
from bot.utils.notifications import send_telegram_notification

async def generate_flow(
    flow_id: int,
    chat_id: int,
) -> None:
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        flow_service = Container.flow_service()
        post_service = Container.post_service()
        flow = await flow_service.get_flow_by_id(flow_id)
        
        if not flow:
            await send_telegram_notification(
                bot_token,
                chat_id,
                f"❌ Флоу з ID {flow_id} не знайдено"
            )
            return

        posts = await _start_telegram_generations(
            flow,
            flow_service,
            post_service
        )
            
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

async def _start_telegram_generations(
    flow,
    flow_service,
    post_service
) -> List:

    existing_posts = await post_service.get_all_posts_in_flow(flow.id)
    existing_count = len(existing_posts)
    
    generated_posts = await post_service.generate_auto_posts(flow.id)
    if not generated_posts:
        logging.info(f"No posts generated for flow {flow.id}")
        return
    
    total_after_generation = existing_count + len(generated_posts)
    overflow = total_after_generation - flow.flow_volume
    
    if overflow > 0:
        posts_to_delete = min(overflow, existing_count)
        if posts_to_delete > 0:
            old_posts = existing_posts[:posts_to_delete]
            logging.info(f"Deleting {len(old_posts)} oldest posts from flow {flow.id}")
            
            for post in old_posts:
                await post_service.delete_post(post.id)
    
    await flow_service.update_next_generation_time(flow.id)

    return generated_posts

if __name__ == "__main__":
    flow_id = int(sys.argv[1])
    chat_id = int(sys.argv[2])
    asyncio.run(generate_flow(flow_id, chat_id))