from admin_panel.admin_panel.models import Draft
from bot.database.exceptions import DraftNotFoundError

class DraftRepository:
    async def create_draft(self, user, post) -> Draft:
        return await Draft.objects.acreate(
            user=user,
            post=post
        )

    async def get_draft_by_id(self, draft_id: int) -> Draft:
        try:
            return await Draft.objects.aget(id=draft_id)
        except Draft.DoesNotExist:
            raise DraftNotFoundError(f"Draft with id={draft_id} not found.")

    async def update_draft(self, draft: Draft) -> Draft:
        await draft.asave()
        return draft

    async def delete_draft(self, draft: Draft):
        await draft.adelete()