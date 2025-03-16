from admin_panel.admin_panel.models import Post, Flow
from database.exceptions import PostNotFoundError

class PostRepository:
    async def create_post(
        self,
        flow: Flow,
        content: str,
        source_url: str = None,
        status="draft",
        scheduled_time=None
    ) -> Post:
        return await Post.objects.acreate(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time
        )

    async def get_posts_by_flow(self, flow: Flow) -> Post:
        return Post.objects.filter(flow=flow)

    async def get_post_by_id(self, post_id):
        try:
            return await Post.objects.aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found.")
        
    async def update_post(self, post: Post) -> Post:
        await post.asave()
        return post
    
    async def delete_post(self, post: Post) -> None:
        await post.adelete()