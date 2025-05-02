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
        logging.info(f"Found {len(flows)} flows due for generation")
        
        for flow in flows:
            logging.info(f"Processing flow {flow.id} (volume: {flow.flow_volume})")
            try:
                existing_count = await post_service.count_posts_in_flow(flow.id)
                posts_dto = await post_service.generate_auto_posts(flow.id)
                
                if not posts_dto:
                    logging.info(f"No posts generated for flow {flow.id}")
                    continue
                
                if existing_count >= flow.flow_volume:
                    old_posts = await post_service.get_oldest_posts(flow.id, len(posts_dto))
                    logging.info(f"Removing {len(old_posts)} old posts for flow {flow.id}")
                    
                    for post in old_posts:
                        await post_service.delete_post(post.id)
                
                created_posts = []
                for post_data in posts_dto:
                    post = await post_service.create_post(
                        flow_id=flow.id,
                        content=post_data.content,
                        media_list=[
                            {'path': img.url, 'type': 'image', 'order': img.order}
                            for img in post_data.images
                        ] + (
                            [{'path': post_data.video_url, 'type': 'video', 'order': len(post_data.images)}]
                            if post_data.video_url else []
                        ),
                        is_auto_generated=True
                    )
                    created_posts.append(post)
                
                if created_posts:
                    logging.info(f"Created {len(created_posts)} new posts for flow {flow.id}")
                    await flow_service.update_next_generation_time(flow.id)
                
            except Exception as e:
                logging.error(f"Error processing flow {flow.id}: {str(e)}")
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
            logging.info(f"Processing flow {flow.id} (content length: {flow.content_length})")
            try:
                generated_posts = await post_service.generate_auto_posts(flow.id)
                
                if not generated_posts:
                    logging.info(f"No posts generated for flow {flow.id}")
                    continue
                
                posts_to_delete = len(generated_posts)
                existing_count = await post_service.count_posts_in_flow(flow.id)
                
                if existing_count > 0:
                    old_posts = await post_service.get_oldest_posts(flow.id, posts_to_delete)
                    logging.info(f"Deleting {len(old_posts)} oldest posts from flow {flow.id}")
                    
                    for post in old_posts:
                        await post_service.delete_post(post.id)
                
                await flow_service.update_next_generation_time(flow.id)
                logging.info(f"Successfully updated flow {flow.id} with {len(generated_posts)} new posts")

            except Exception as e:
                logging.error(f"Error processing flow {flow.id}: {str(e)}")
                self.retry(exc=e, countdown=60)

    asyncio.run(_async_wrapper())