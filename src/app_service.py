from typing import List
from injector import inject
from src.data_feeds.base_feed import BaseDataFeed
from src.dto.provider_requests import FeedId, FeedValueData, FeedVolumeData


class AppService:
    @inject
    def __init__(self, data_feed: BaseDataFeed):
        self.data_feed = data_feed

    async def get_value(self, feed: FeedId) -> FeedValueData:
        return await self.data_feed.get_value(feed)

    async def get_values(self, feeds: List[FeedId]) -> List[FeedValueData]:
        return await self.data_feed.get_values(feeds)

    async def get_volumes(self, feeds: List[FeedId], volume_window: int) -> List[FeedVolumeData]:
        return await self.data_feed.get_volumes(feeds, volume_window)