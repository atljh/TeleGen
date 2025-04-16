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
                await post_service.generate_auto_posts(flow.id)
                await flow_service.update_next_generation_time(flow.id)
            except Exception as e:
                self.retry(exc=e, countdown=60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_wrapper())
    finally:
        loop.close()

@shared_task(bind=True, name="force_flows_generation_task")
def force_flows_generation_task(self):
    async def _async_wrapper():
        logging.info("START FORCE GENERATION")
        flow_service = Container.flow_service()
        post_service = Container.post_service()
        userbot_service = Container.userbot_service()

        flows = await flow_service.force_flows_due_for_generation()
        logging.info(f"Flows for force generation: {len(flows)}")
        
        for flow in flows:
            try:
                existing_count = await post_service.count_posts_in_flow(flow.id)
                if existing_count >= flow.flow_volume:
                    logging.info(f"Skipping flow {flow.id} - reached max posts")
                    continue
                    
                await post_service.generate_auto_posts(flow.id)
                await flow_service.update_next_generation_time(flow.id)
                logging.info(f"Successfully generated posts for flow {flow.id}")
            except Exception as e:
                logging.error(f"Error processing flow {flow.id}: {str(e)}")
                self.retry(exc=e, countdown=60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_wrapper())
    finally:
        loop.close()
