from datetime import datetime
from typing import Optional, List, AsyncGenerator
from admin_panel.admin_panel.models import Post, Flow
from bot.database.exceptions import PostNotFoundError, InvalidOperationError


class PostRepository:
    async def create(
        self,
        flow: Flow,
        content: str,
        source_url: Optional[str] = None,
        status: str = "draft",
        scheduled_time: Optional[datetime] = None,
        media_url: Optional[str] = None
    ) -> Post:
        """Создает новый пост с валидацией"""
        if scheduled_time and scheduled_time < datetime.now():
            raise InvalidOperationError("Scheduled time cannot be in the past")
            
        return await Post.objects.acreate(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time,
            media_url=media_url
        )

    async def get(self, post_id: int) -> Post:
        """Получает пост по ID"""
        try:
            return await Post.objects.select_related('flow').aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found")

    async def exists(self, post_id: int) -> bool:
        """Проверяет существование поста"""
        return await Post.objects.filter(id=post_id).aexists()

    async def list(
        self,
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        is_published: Optional[bool] = None,
        scheduled_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Post]:
        """Получает список постов с фильтрацией"""
        query = Post.objects.all()
        
        if flow_id:
            query = query.filter(flow_id=flow_id)
        if status:
            query = query.filter(status=status)
        if is_published is not None:
            query = query.filter(is_published=is_published)
        if scheduled_before:
            query = query.filter(scheduled_time__lte=scheduled_before)
            
        return [
            post async for post in 
            query.select_related('flow')
                .order_by('-created_at')
                [offset:offset+limit]
        ]

    async def stream_posts(
        self,
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        batch_size: int = 50
    ) -> AsyncGenerator[List[Post], None]:
        """Потоковая выгрузка постов"""
        query = Post.objects.all()
        if flow_id:
            query = query.filter(flow_id=flow_id)
        if status:
            query = query.filter(status=status)
            
        offset = 0
        while True:
            batch = await self.list(
                flow_id=flow_id,
                status=status,
                limit=batch_size,
                offset=offset
            )
            if not batch:
                break
            yield batch
            offset += batch_size

    async def update(
        self,
        post_id: int,
        **fields
    ) -> Post:
        """Обновляет пост"""
        post = await self.get(post_id)
        for field, value in fields.items():
            setattr(post, field, value)
        await post.asave()
        return post

    async def delete(self, post_id: int) -> None:
        """Удаляет пост"""
        post = await self.get(post_id)
        await post.adelete()

    async def count(
        self,
        flow_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """Считает количество постов"""
        query = Post.objects.all()
        if flow_id:
            query = query.filter(flow_id=flow_id)
        if status:
            query = query.filter(status=status)
        return await query.acount()

    async def get_scheduled_posts(self, before: datetime) -> List[Post]:
        """Получает запланированные посты"""
        return await self.list(
            status='scheduled',
            scheduled_before=before
        )