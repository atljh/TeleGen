from admin_panel.admin_panel.models import Post
from database.exceptions import PostNotFoundError
from database.utils.async_orm import AsyncORM


class PostManager(AsyncORM):
    def create_post(self, flow, content, source_url=None, status="draft", scheduled_time=None):
        post = Post.objects.create(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time
        )
        return post

    def get_posts_by_flow(self, flow):
        return Post.objects.filter(flow=flow)

    def get_post_by_id(self, post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found.")

    def update_post_status(self, post_id, status):
        post = PostManager.get_post_by_id(post_id)
        post.status = status
        post.save()
        return post

    def delete_post(self, post_id):
        post = PostManager.get_post_by_id(post_id)
        post.delete()
