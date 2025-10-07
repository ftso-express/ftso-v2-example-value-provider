from typing import List
from loguru import logger
from src.data_feeds.base_feed import BaseDataFeed
from src.dto.provider_requests import FeedId, FeedValueData, FeedVolumeData

DEFAULT_VALUE = 0.01


class FixedFeed(BaseDataFeed):
    def __init__(self):
        logger.warning(f"Initializing FixedFeed, will return {DEFAULT_VALUE} for all feeds.")

    async def get_value(self, feed: FeedId) -> FeedValueData:
        return FeedValueData(feed=feed, value=DEFAULT_VALUE)

    async def get_values(self, feeds: List[FeedId]) -> List[FeedValueData]:
        return [await self.get_value(feed) for feed in feeds]

    async def get_volumes(self, feeds: List[FeedId], volume_window: int) -> List[FeedVolumeData]:
        return []