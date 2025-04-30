import logging
from celery import shared_task
from bot.containers import Container
import asyncio

@shared_task(bind=True) 
def check_flows_generation(self):
    async def _async_wrapper():
        flow_service = Container.flow_service()
        post_service = Container.post_service()

        flows = await flow_service.get_flows_due_for_generation()
        for flow in flows:
            try:
                posts = await post_service.generate_auto_posts(flow.id)
                if posts:
                    await flow_service.update_next_generation_time(flow.id)
            except Exception as e:
                logging.error(f"Error in flow {flow.id}: {str(e)}")
                self.retry(exc=e, countdown=60)

    asyncio.run(_async_wrapper())


@shared_task(bind=True, name="force_flows_generation_task")
def force_flows_generation_task(self):
    async def _async_wrapper():
        flow_service = Container.flow_service()
        post_service = Container.post_service()

        flows = await flow_service.force_flows_due_for_generation()
        logging.info(f"Flows for force generation: {len(flows)}")
        
        for flow in flows:
            logging.info(flow.content_length)
            try:
                existing_count = await post_service.count_posts_in_flow(flow.id)
                posts_dto = await post_service.userbot_service.get_last_posts(flow)
                
                if not posts_dto:
                    continue
                
                if existing_count >= flow.flow_volume:
                    # Отримуємо старі пости для оновлення
                    old_posts = await post_service.get_oldest_posts(flow.id, len(posts_dto))
                    logging.info(f"Updating {len(old_posts)} old posts for flow {flow.id}")
                    
                    # Оновлюємо старі пости
                    for i, post in enumerate(old_posts):
                        if i >= len(posts_dto):
                            break
                        await post_service.update_post_with_media(
                            post_id=post.id,
                            content=posts_dto[i].content,
                            media_list=[
                                {'path': img.url, 'type': 'image', 'order': img.order}
                                for img in posts_dto[i].images
                            ] + (
                                [{'path': posts_dto[i].video_url, 'type': 'video', 'order': len(posts_dto[i].images)}]
                                if posts_dto[i].video_url else []
                            )
                        )
                else:
                    # Створюємо нові пости
                    generated_posts = await post_service.generate_auto_posts(flow.id)
                    if generated_posts:
                        logging.info(f"Generated {len(generated_posts)} new posts for flow {flow.id}")
                
                # Оновлюємо час наступної генерації
                await flow_service.update_next_generation_time(flow.id)
                
            except Exception as e:
                logging.error(f"Error processing flow {flow.id}: {str(e)}")
                self.retry(exc=e, countdown=60)

    asyncio.run(_async_wrapper())