import random
from typing import List
from data_feeds.base_feed import BaseDataFeed
from dto.provider_requests import FeedId, FeedValueData, FeedVolumeData

BASE_VALUE = 0.05


class RandomFeed(BaseDataFeed):
    async def get_value(self, feed: FeedId) -> FeedValueData:
        return FeedValueData(feed=feed, value=BASE_VALUE * (0.5 + random.random()))

    async def get_values(self, feeds: List[FeedId]) -> List[FeedValueData]:
        return [await self.get_value(feed) for feed in feeds]

    async def get_volumes(self, feeds: List[FeedId], volume_window: int) -> List[FeedVolumeData]:
        return []