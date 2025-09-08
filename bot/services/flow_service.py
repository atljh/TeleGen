import logging
from datetime import timedelta
from typing import Any, Optional

from asgiref.sync import sync_to_async
from django.utils import timezone

from bot.database.exceptions import FlowNotFoundError
from bot.database.models.flow import ContentLength, FlowDTO, GenerationFrequency
from bot.database.models.user import UserDTO
from bot.database.repositories import ChannelRepository, FlowRepository
from bot.services.logger_service import get_logger
from bot.services.web.rss_service import RssService


class FlowService:
    def __init__(
        self,
        flow_repository: FlowRepository,
        channel_repository: ChannelRepository,
        rss_service: RssService,
    ):
        self.flow_repository = flow_repository
        self.channel_repository = channel_repository
        self.rss_service = rss_service
        self.logger = get_logger()

    async def create_flow(
        self,
        channel_id: int,
        name: str,
        theme: str,
        sources: list[dict],
        content_length: ContentLength | str,
        use_emojis: bool,
        use_premium_emojis: bool,
        title_highlight: bool,
        cta: bool,
        frequency: GenerationFrequency | str,
        signature: str | None = None,
        flow_volume: int = 5,
        ad_time: str | None = None,
    ) -> FlowDTO:
        channel = await self.channel_repository.get_channel_by_id(channel_id)

        if isinstance(content_length, ContentLength):
            content_length = content_length.value

        if isinstance(frequency, GenerationFrequency):
            frequency = frequency.value
        try:
            flow = await self.flow_repository.create_flow(
                channel=channel,
                name=name,
                theme=theme,
                sources=sources,
                content_length=content_length,
                use_emojis=use_emojis,
                use_premium_emojis=use_premium_emojis,
                title_highlight=title_highlight,
                cta=cta,
                frequency=frequency,
                signature=signature,
                flow_volume=flow_volume,
                ad_time=ad_time,
            )
        except Exception as e:
            logging.error(f"Flow error {e}", exc_info=True)
            return
        try:
            flow_dto = FlowDTO.from_orm(flow)
        except Exception as e:
            logging.error(f"DTO conversion error: {e}", exc_info=True)
            return
        return FlowDTO.from_orm(flow)

    async def get_flow_by_channel_id(self, channel_id: int) -> FlowDTO | None:
        try:
            return await self.flow_repository.get_flow_by_channel_id(channel_id)
        except FlowNotFoundError:
            return None

    async def get_flow_by_id(self, flow_id: int) -> FlowDTO:
        try:
            flow = await self.flow_repository.get_flow_by_id(flow_id)
            return FlowDTO.from_orm(flow)
        except Exception as e:
            logging.error(f"Error getting flow {flow_id}: {e}")
            raise

    async def get_user_flows(self, user_id: int) -> list[FlowDTO]:
        try:
            flows = await self.flow_repository.get_user_flows(user_id)
            return [FlowDTO.from_orm(f) for f in flows]
        except Exception as e:
            logging.error(f"Error getting flows for user {user_id}: {e}")
            raise

    async def update_flow(self, flow_id: int, **kwargs) -> FlowDTO:
        try:
            flow = await self.flow_repository.get_flow_by_id(flow_id)
            if not flow:
                raise FlowNotFoundError(f"Flow with ID {flow_id} not found")

            old_values = self._get_old_values(flow, kwargs.keys())

            for field, value in kwargs.items():
                setattr(flow, field, value)

            updated_flow = await self.flow_repository.update_flow(flow)

            await self._log_flow_update(flow, old_values, kwargs)

            return FlowDTO.from_orm(updated_flow)

        except Exception as e:
            logging.error(f"Error updating flow {flow_id}: {e}")
            raise

    def _get_old_values(self, flow, fields_to_update) -> dict[str, Any]:
        old_values = {}
        for field in fields_to_update:
            if hasattr(flow, field):
                old_values[field] = getattr(flow, field)
        return old_values

    async def _log_flow_update(self, flow, old_values: dict, new_values: dict):
        if not self.logger:
            return

        try:
            channel = await self.channel_repository.get_channel(flow.channel_id)
            user = await sync_to_async(lambda: channel.user)()

            changes = self._format_changes_for_log(old_values, new_values)

            if changes:
                await self.logger.settings_updated(
                    user=user,
                    setting_type="flow",
                    old_value=changes["old"],
                    new_value=changes["new"],
                    additional_data={
                        "flow_id": flow.id,
                        "flow_name": flow.name,
                        "changed_fields": list(new_values.keys()),
                    },
                )

        except Exception as e:
            logging.error(f"Error logging flow update: {e}")

    def _format_changes_for_log(
        self, old_values: dict, new_values: dict
    ) -> Optional[dict]:
        if not old_values or not new_values:
            return None

        formatted_old = []
        formatted_new = []

        for field, new_value in new_values.items():
            old_value = old_values.get(field)

            if old_value == new_value:
                continue

            formatted_old.append(f"{field}: {self._format_value(old_value)}")
            formatted_new.append(f"{field}: {self._format_value(new_value)}")

        if not formatted_old or not formatted_new:
            return None

        return {"old": "\n".join(formatted_old), "new": "\n".join(formatted_new)}

    def _format_value(self, value) -> str:
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return "✅" if value else "❌"
        elif isinstance(value, (list, dict)):
            return str(len(value)) if value else "Empty"
        elif isinstance(value, str) and len(value) > 50:
            return f"{value[:50]}..."
        else:
            return str(value)

    async def delete_flow(self, flow_id: int):
        try:
            flow = await self.flow_repository.get_flow_by_id(flow_id)
            await self.flow_repository.delete_flow(flow)
            logging.info(f"Deleted flow {flow_id}")
        except Exception as e:
            logging.error(f"Error deleting flow {flow_id}: {e}")
            raise

    async def get_flows_due_for_generation(self) -> list[FlowDTO]:
        now = timezone.now()
        flows = await self.flow_repository.list(
            next_generation_time__lte=now, include_null_generation_time=True, limit=None
        )
        return flows

    async def force_flows_due_for_generation(self) -> list[FlowDTO]:
        flows = await self.flow_repository.list()
        return flows

    async def update_next_generation_time(self, flow_id: int):
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        if flow.frequency == "hourly":
            next_time = timezone.now() + timedelta(hours=1)
        elif flow.frequency == "12h":
            next_time = timezone.now() + timedelta(hours=12)
        elif flow.frequency == "daily":
            next_time = timezone.now() + timedelta(days=1)
        else:
            next_time = None

        await self.update_flow(
            flow.id, next_generation_time=next_time, last_generated_at=timezone.now()
        )

    async def get_or_set_source_rss_url(self, flow_id: int, link: str) -> str | None:
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        if not flow:
            raise FlowNotFoundError(f"Flow with ID {flow_id} not found")

        source = next((s for s in flow.sources if s.get("link") == link), None)
        if not source:
            raise ValueError(f"Source with link {link} not found in flow {flow_id}")

        if source.get("type") != "web":
            return None

        if source.get("rss_url"):
            return source["rss_url"]

        rss_url = await self.rss_service._discover_rss_for_source(source)
        if not rss_url:
            logging.warning(f"No RSS feed found for web link {link}")
            return None

        updated_sources = [
            (
                {**s, "rss_url": rss_url}
                if s.get("link") == link and s.get("type") == "web"
                else s
            )
            for s in flow.sources
        ]
        await self.update_flow(flow_id, sources=updated_sources)
        return rss_url

    async def get_user_by_flow_id(self, flow_id: int) -> UserDTO:
        flow = await self.get_flow_by_id(flow_id)
        channel = await self.channel_repository.get_channel(flow.channel_id)
        user = await sync_to_async(lambda: channel.user)()
        return UserDTO.from_orm(user)
