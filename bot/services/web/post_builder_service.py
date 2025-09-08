from datetime import datetime
import logging
from bot.database.models import FlowDTO, PostDTO, PostImageDTO, PostStatus


class PostBuilderService:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

    def build_post(
        self, raw_data: dict, processed_content: str, flow: FlowDTO
    ) -> PostDTO:
        signature = f"\n\n{flow.signature}" if flow.signature else ""

        return PostDTO(
            id=None,
            flow_id=flow.id,
            content=f"{processed_content}{signature}",
            source_id=raw_data["source_id"],
            source_url=raw_data["source_url"],
            original_link=raw_data["original_link"],
            original_date=raw_data["original_date"],
            created_at=datetime.now(),
            status=PostStatus.DRAFT,
            images=[PostImageDTO(url=img) for img in raw_data.get("images", [])],
            media_type="image" if raw_data.get("images") else None,
        )
