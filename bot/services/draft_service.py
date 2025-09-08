import logging

from admin_panel.admin_panel.models import User
from bot.database.exceptions import PostNotFoundError, UserNotFoundError
from bot.database.models import DraftDTO, PostDTO, UserDTO
from bot.database.repositories import DraftRepository, PostRepository, UserRepository


class DraftService:
    def __init__(
        self,
        draft_repository: DraftRepository,
        post_repository: PostRepository,
        user_repository: UserRepository,
        logger: logging.Logger | None = None,
    ):
        self.draft_repository = draft_repository
        self.post_repository = post_repository
        self.user_repository = user_repository
        self.logger = logger or logging.getLogger(__name__)

    async def create_draft(self, telegram_id: int, post_id: int) -> DraftDTO:
        try:
            user = await self.user_repository.get_user_by_telegram_id(telegram_id)
            post = await self.post_repository.get_post_by_id(post_id)

            draft = await self.draft_repository.create_draft(user=user, post=post)
            return draft
        except UserNotFoundError:
            raise UserNotFoundError(f"User with telegram_id={telegram_id} not found.")
        except PostNotFoundError:
            raise PostNotFoundError(f"Post with id={post_id} not found.")

    async def get_draft_by_id(self, draft_id: int) -> DraftDTO:
        draft = await self.draft_repository.get_draft_by_id(draft_id)
        return DraftDTO.from_orm(draft)

    async def update_draft(self, draft_id: int) -> DraftDTO:
        draft = await self.draft_repository.get_draft_by_id(draft_id)
        updated_draft = await self.draft_repository.update_draft(draft)
        return DraftDTO.from_orm(updated_draft)

    async def delete_draft(self, draft_id: int):
        draft = await self.draft_repository.get_draft_by_id(draft_id)
        await self.draft_repository.delete_draft(draft)
