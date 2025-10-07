from pydantic import BaseModel
from typing import List


class FeedId(BaseModel):
    category: int
    name: str


class Volume(BaseModel):
    exchange: str
    volume: float


class FeedValuesRequest(BaseModel):
    feeds: List[FeedId]


class FeedValueData(BaseModel):
    feed: FeedId
    value: float


class FeedVolumeData(BaseModel):
    feed: FeedId
    volumes: List[Volume]


class RoundFeedValuesResponse(BaseModel):
    votingRoundId: int
    data: List[FeedValueData]


class FeedValuesResponse(BaseModel):
    data: List[FeedValueData]


class FeedVolumesResponse(BaseModel):
    data: List[FeedVolumeData]