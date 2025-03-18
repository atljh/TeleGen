from admin_panel.admin_panel.models import Post, Flow
from bot.database.exceptions import PostNotFoundError

class PostRepository:
    async def create_post(
        self,
        flow: Flow,
        content: str,
        source_url: str | None = None,
        status: str = "draft",
        scheduled_time=None
    ) -> Post:
        return await Post.objects.acreate(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time
        )

    async def get_post_by_id(self, post_id: int) -> Post:
        try:
            return await Post.objects.aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found.")

    async def update_post(self, post: Post) -> Post:
        await post.asave()
        return post

    async def delete_post(self, post: Post):
        await post.adelete()