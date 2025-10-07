from fastapi import Body, Query, Path
from pynest.common import Controller, Post, Inject, DefaultValuePipe, ParseIntPipe
from loguru import logger
from typing import Annotated

from src.app_service import AppService
from src.dto.provider_requests import (
    FeedValuesRequest,
    FeedValuesResponse,
    FeedVolumesResponse,
    RoundFeedValuesResponse,
)


@Controller()
class AppController:
    @Inject()
    def __init__(self, app_service: AppService):
        self.app_service = app_service
        self.logger = logger

    @Post("feed-values/{voting_round_id}")
    async def get_feed_values(
        self,
        voting_round_id: Annotated[int, Path(alias="voting_round_id")],
        body: FeedValuesRequest = Body(...),
    ) -> RoundFeedValuesResponse:
        values = await self.app_service.get_values(body.feeds)
        self.logger.info(f"Feed values for voting round {voting_round_id}: {values}")
        return RoundFeedValuesResponse(votingRoundId=voting_round_id, data=values)

    @Post("feed-values")
    async def get_current_feed_values(self, body: FeedValuesRequest = Body(...)) -> FeedValuesResponse:
        values = await self.app_service.get_values(body.feeds)
        self.logger.info(f"Current feed values: {values}")
        return FeedValuesResponse(data=values)

    @Post("volumes")
    async def get_feed_volumes(
        self,
        body: FeedValuesRequest = Body(...),
        window_sec: int = Query(60, alias="window"),
    ) -> FeedVolumesResponse:
        values = await self.app_service.get_volumes(body.feeds, window_sec)
        self.logger.info(f"Feed volumes for last {window_sec} seconds: {values}")
        return FeedVolumesResponse(data=values)