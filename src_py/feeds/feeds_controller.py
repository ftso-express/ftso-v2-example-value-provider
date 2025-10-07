from nest.core import Controller, Get, Post, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import config


from .feeds_service import FeedsService
from .feeds_model import Feeds


@Controller("feeds", tag="feeds")
class FeedsController:

    def __init__(self, feeds_service: FeedsService):
        self.feeds_service = feeds_service

    @Get("/")
    async def get_feeds(self, session: AsyncSession = Depends(config.get_db)):
        return await self.feeds_service.get_feeds(session)

    @Post("/")
    async def add_feeds(self, feeds: Feeds, session: AsyncSession = Depends(config.get_db)):
        return await self.feeds_service.add_feeds(feeds, session)
 