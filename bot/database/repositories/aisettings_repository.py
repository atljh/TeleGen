from admin_panel.admin_panel.models import AISettings
from bot.database.exceptions import AISettingsNotFoundError

class AISettingsRepository:
    async def create_ai_settings(self, user, prompt: str, style: str) -> AISettings:
        return await AISettings.objects.acreate(
            user=user,
            prompt=prompt,
            style=style
        )

    async def get_ai_settings_by_id(self, ai_settings_id: int) -> AISettings:
        try:
            return await AISettings.objects.aget(id=ai_settings_id)
        except AISettings.DoesNotExist:
            raise AISettingsNotFoundError(f"AISettings with id={ai_settings_id} not found.")

    async def update_ai_settings(self, ai_settings: AISettings) -> AISettings:
        await ai_settings.asave()
        return ai_settings

    async def delete_ai_settings(self, ai_settings: AISettings):
        await ai_settings.adelete()