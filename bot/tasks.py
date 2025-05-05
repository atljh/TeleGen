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
def force_flows_generation_task(self, flow_id: int):
    async def _async_wrapper():
        flow_service = Container.flow_service()
        post_service = Container.post_service()

        try:
            flow = await flow_service.get_flow_by_id(flow_id)
            if not flow:
                raise Exception(f"Флоу с ID {flow_id} не найден")

            logging.info(f"Processing flow {flow.id} (volume: {flow.flow_volume})")
            
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
            logging.info(f"Flow {flow.id} updated. Current posts: {existing_count - (overflow if overflow > 0 else 0) + len(generated_posts)}")

        except Exception as e:
            logging.error(f"Error processing flow {flow_id}: {str(e)}")
            self.retry(exc=e, countdown=60)

    asyncio.run(_async_wrapper())