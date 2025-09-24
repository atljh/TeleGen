import asyncio
import logging

from bot.services.flow_service import FlowService
from bot.services.web.rss_service import RssService, SourceDict

logger = logging.getLogger(__name__)


class RssUrlManager:
    def __init__(self, rss_service: RssService, flow_service: FlowService):
        self.rss_service = rss_service
        self.flow_service = flow_service

    async def get_or_set_rss_url(
        self, flow_id: int, source: SourceDict, *, force_refresh: bool = False
    ) -> str | None:
        try:
            if force_refresh:
                if new_url := await self._discover_and_cache(flow_id, source):
                    return new_url
                return None

            return await self.flow_service.get_or_set_source_rss_url(
                flow_id, source["link"]
            )

        except Exception as e:
            logger.error(
                f"Failed to get/set RSS URL for {source.get('link')}: {e}",
                exc_info=True,
            )
            return None

    async def batch_process_sources(
        self,
        flow_id: int,
        sources: list[SourceDict],
        *,
        parallel: bool = True,
        force_refresh: bool = False,
    ) -> list[str]:
        async def process_source(source: SourceDict) -> str | None:
            return await self.get_or_set_rss_url(
                flow_id, source, force_refresh=force_refresh
            )

        if parallel:
            tasks = [process_source(s) for s in sources]
            results = await asyncio.gather(*tasks)
            return [url for url in results if url]

        return [url for source in sources if (url := await process_source(source))]

    async def _discover_and_cache(self, flow_id: int, source: SourceDict) -> str | None:
        try:
            if discovered_url := await self.rss_service._discover_rss_for_source(
                source
            ):
                await self.flow_service.get_or_set_source_rss_url(
                    flow_id, source["link"], rss_url=discovered_url
                )
                return discovered_url
            return None
        except Exception as e:
            logger.error(f"Discovery failed for {source.get('link')}: {e}")
            return None
