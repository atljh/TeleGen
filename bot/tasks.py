import logging
from celery import shared_task
from bot.containers import Container
import asyncio

@shared_task(bind=True)
def check_flows_generation(self):
    async def _async_wrapper():
        container = Container()
        await container.init_resources()
        
        flow_service = container.flow_service()
        post_service = container.post_service()
        userbot_service = container.userbot_service()
        
        await userbot_service.initialize()

        flows = await flow_service.get_flows_due_for_generation()
        for flow in flows:
            try:
                existing_count = await post_service.count_posts_in_flow(flow.id)
                if existing_count >= flow.flow_volume:
                    continue
                    
                await post_service.generate_auto_posts(flow.id)
                await flow_service.update_next_generation_time(flow.id)
            except Exception as e:
                logging.error(f"Error processing flow {flow.id}: {e}")
                self.retry(exc=e, countdown=60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_wrapper())
    finally:
        loop.close()