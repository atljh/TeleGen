import logging
from celery import shared_task
from bot.containers import Container
import asyncio

@shared_task(bind=True) 
def check_flows_generation(self):
    async def _async_wrapper():
        container = Container()
        flow_service = container.flow_service()
        post_service = container.post_service()

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
        container = Container()
        flow_service = container.flow_service()
        post_service = container.post_service()

        flows = await flow_service.force_flows_due_for_generation()
        logging.info(f"Flows for force generation: {len(flows)}")
        
        for flow in flows:
            try:
                existing_count = await post_service.count_posts_in_flow(flow.id)
                if existing_count >= flow.flow_volume:
                    logging.info(f"Skipping flow {flow.id} - reached max posts")
                    continue
                    
                posts = await post_service.generate_auto_posts(flow.id)
                if posts:
                    await flow_service.update_next_generation_time(flow.id)
                    logging.info(f"Generated {len(posts)} posts for flow {flow.id}")
            except Exception as e:
                logging.error(f"Error processing flow {flow.id}: {str(e)}")
                self.retry(exc=e, countdown=60)

    asyncio.run(_async_wrapper())