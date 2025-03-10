from admin_panel.admin_panel.models import Post
from database.exceptions import PostNotFoundError


class PostManager:
    @staticmethod
    def create_post(flow, content, source_url=None, status="draft", scheduled_time=None):
        post = Post.objects.create(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time
        )
        return post

    @staticmethod
    def get_posts_by_flow(flow):
        return Post.objects.filter(flow=flow)

    @staticmethod
    def get_post_by_id(post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found.")

    @staticmethod
    def update_post_status(post_id, status):
        post = PostManager.get_post_by_id(post_id)
        post.status = status
        post.save()
        return post

    @staticmethod
    def delete_post(post_id):
        post = PostManager.get_post_by_id(post_id)
        post.delete()
