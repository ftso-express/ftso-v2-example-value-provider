from abc import ABC, abstractmethod
from typing import List
from src.dto.provider_requests import FeedId, FeedValueData, FeedVolumeData


class BaseDataFeed(ABC):
    @abstractmethod
    async def get_value(self, feed: FeedId) -> FeedValueData:
        pass

    @abstractmethod
    async def get_values(self, feeds: List[FeedId]) -> List[FeedValueData]:
        pass

    @abstractmethod
    async def get_volumes(self, feeds: List[FeedId], volume_window: int) -> List[FeedVolumeData]:
        pass