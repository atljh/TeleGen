from datetime import datetime
from typing import Optional

from asgiref.sync import sync_to_async

from admin_panel.admin_panel.models import Post, PostImage
from bot.database.exceptions import PostNotFoundError
from bot.database.models import PostDTO, PostStatus
from bot.database.repositories import PostRepository


class PostBaseService:
    def __init__(self, post_repository: PostRepository):
        self.post_repo = post_repository

    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        images = await sync_to_async(
            lambda: list(post.images.all().order_by("order"))
        )()

        dto = PostDTO.from_orm(post)
        dto.images = images
        return dto


    async def create_post(
        self,
        flow,
        content: str,
        original_content: str,
        original_link: str,
        original_date: datetime,
        source_url: Optional[str] = None,
        media_list: Optional[list[str]] = None,
    ) -> PostDTO:
        post = await self.post_repo.create_with_media(
            flow=flow,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_url=source_url,
            content=content,
            media_list=media_list,
        )
        return PostDTO.from_orm(post)

    async def update_post(
        self,
        post_id: int,
        content: Optional[str] = None,
        images: Optional[list[dict]] = None,
        publication_date: Optional[datetime] = None,
        status: Optional[PostStatus] = None,
        video_url: Optional[str] = None,
    ) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        if content is not None:
            post.content = content
        if publication_date:
            post.publication_date = publication_date
        if status:
            post.status = status
        if video_url is not None:
            post.video_url = video_url

        if images is not None:
            await self._update_post_images(post, images)

        await sync_to_async(post.save)()
        return PostDTO.from_orm(post)

    async def _update_post_images(self, post: Post, images: list[dict]) -> None:
        await sync_to_async(lambda: post.images.all().delete())()
        for img_data in images:
            await sync_to_async(PostImage.objects.create)(
                post=post,
                image=img_data["file_path"],
                order=img_data["order"],
            )

    async def delete_post(self, post_id: int) -> None:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")
        await self.post_repo.delete(post_id)


    async def get_all_posts_in_flow(
        self, flow_id: int, status: PostStatus
    ) -> list[PostDTO]:
        posts = await self.post_repo.list(flow_id=flow_id, status=status)

        posts = await sync_to_async(list)(posts)

        result = []
        for post in posts:
            images = await sync_to_async(
                lambda p=post: list(p.images.all().order_by("order"))
            )()
            dto = PostDTO.from_orm(post)
            dto.images = images
            result.append(dto)

        return result
