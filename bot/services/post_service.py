from bot.database.dtos import PostDTO, FlowDTO
from bot.database.repositories import PostRepository, FlowRepository

class PostService:
    def __init__(self, post_repository: PostRepository, flow_repository: FlowRepository):
        self.post_repository = post_repository
        self.flow_repository = flow_repository

    async def create_post(
        self,
        flow_id: int,
        content: str,
        source_url: str | None = None,
        status: str = "draft",
        scheduled_time = None
    ) -> PostDTO:
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        post = await self.post_repository.create_post(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time
        )
        return PostDTO.from_orm(post)
    
    async def get_post_by_id(self, post_id: int) -> PostDTO:
        post = await self.post_repository.get_post_by_id(post_id)
        return PostDTO.from_orm(post)
    
    async def get_posts_by_flow_id(self, flow_id: int) -> list[PostDTO]:
        posts = await self.post_repository.get_posts_by_flow_id(flow_id=flow_id)
        return [PostDTO.from_orm(post) for post in posts]

    async def update_post(self, post_id: int) -> PostDTO:
        post = await self.post_repository.get_post_by_id(post_id)
        updated_post = await self.post_repository.update_post(post=post)
        return PostDTO.from_orm(updated_post)
    
    async def delete_post(self, post_id: int):
        post = await self.post_repository.get_post_by_id(post_id)
        await self.post_repository.delete_post(post)