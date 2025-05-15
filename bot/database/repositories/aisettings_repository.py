from admin_panel.admin_panel.models import AISettings
from bot.database.exceptions import AISettingsNotFoundError

class AISettingsRepository:
    async def create_ai_settings(self, flow, prompt: str, style: str) -> AISettings:
        aisettings, created = await AISettings.objects.aget_or_create(
            flow=flow,
            prompt=prompt,
            style=style
        )
        return aisettings.prompt

    async def get_ai_settings_by_id(self, ai_settings_id: int) -> AISettings:
        try:
            return await AISettings.objects.aget(id=ai_settings_id)
        except AISettings.DoesNotExist:
            raise AISettingsNotFoundError(f"AISettings with id={ai_settings_id} not found.")

    async def get_ai_settings_by_flow(self, flow) -> AISettings:

        try:
            return await AISettings.objects.aget(flow=flow)
        except AISettings.DoesNotExist:
            raise AISettingsNotFoundError(f"AISettings with flow={flow} not found.")

    async def update_ai_settings(self, ai_settings: AISettings) -> AISettings:
        await ai_settings.asave()
        return ai_settings

    async def delete_ai_settings(self, ai_settings: AISettings):
        await ai_settings.adelete()