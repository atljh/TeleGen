from admin_panel.admin_panel.models import Post
from database.exceptions import PostNotFoundError

class PostRepository:
    async def create_post(self, flow, content, source_url=None, status="draft", scheduled_time=None):
        return await Post.objects.aget_or_create(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time
        )

    def get_posts_by_flow(self, flow):
        return Post.objects.filter(flow=flow)

    async def get_post_by_id(self, post_id):
        try:
            return await Post.objects.aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found.")