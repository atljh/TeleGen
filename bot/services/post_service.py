from datetime import datetime
from typing import Optional, List
from bot.database.dtos import PostDTO, FlowDTO
from bot.database.repositories import PostRepository, FlowRepository
from bot.database.exceptions import PostNotFoundError, InvalidOperationError

class PostService:
    def __init__(self, post_repository: PostRepository, flow_repository: FlowRepository):
        self.post_repo = post_repository
        self.flow_repo = flow_repository

    async def create_post(
        self,
        flow_id: int,
        content: str,
        source_url: Optional[str] = None,
        status: str = "draft",
        scheduled_time: Optional[datetime] = None,
        media_url: Optional[str] = None
    ) -> PostDTO:

        if not await self.flow_repo.exists(flow_id):
            raise PostNotFoundError(f"Flow with id {flow_id} not found")
        
        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        post = await self.post_repo.create(
            flow_id=flow_id,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time,
            media_url=media_url
        )
        return PostDTO.from_orm(post)
    
    async def get_post(self, post_id: int) -> PostDTO:
        post = await self.post_repo.get(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        return PostDTO.from_orm(post)
    
    async def get_posts_by_flow_id(self, flow_id: int) -> list[PostDTO]:
        posts = await self.post_repo.get_posts_by_flow_id(flow_id=flow_id)
        return [PostDTO.from_orm(post) for post in posts]

    async def list_posts(
        self, 
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PostDTO]:
        posts = await self.post_repo.list(
            flow_id=flow_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [PostDTO.from_orm(post) for post in posts]

    async def update_post(
        self,
        post_id: int,
        content: Optional[str] = None,
        status: Optional[str] = None,
        source_url: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        media_url: Optional[str] = None
    ) -> PostDTO:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")

        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")

        updated_post = await self.post_repo.update(
            post_id=post_id,
            content=content,
            status=status,
            source_url=source_url,
            scheduled_time=scheduled_time,
            media_url=media_url
        )
        return PostDTO.from_orm(updated_post)
    
    async def publish_post(self, post_id: int) -> PostDTO:
        post = await self.get_post(post_id)
        if post.status == "published":
            raise InvalidOperationError("Post is already published")
    
        return await self.update_post(
            post_id=post_id,
            status="published",
            scheduled_time=None
        )
    
    async def delete_post(self, post_id: int) -> None:
        if not await self.post_repo.exists(post_id):
            raise PostNotFoundError(f"Post with id {post_id} not found")
        await self.post_repo.delete(post_id)

    async def get_scheduled_posts(self) -> List[PostDTO]:
        posts = await self.post_repo.list(
            status="scheduled",
            scheduled_time_lt=datetime.now()
        )
        return [PostDTO.from_orm(post) for post in posts]