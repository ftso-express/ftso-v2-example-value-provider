from .feeds_model import Feeds
from .feeds_entity import Feeds as FeedsEntity
from nest.core.decorators.database import async_db_request_handler
from nest.core import Injectable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@Injectable
class FeedsService:

    @async_db_request_handler
    async def add_feeds(self, feeds: Feeds, session: AsyncSession):
        new_feeds = FeedsEntity(
            **feeds.dict()
        )
        session.add(new_feeds)
        await session.commit()
        return new_feeds.id

    @async_db_request_handler
    async def get_feeds(self, session: AsyncSession):
        query = select(FeedsEntity)
        result = await session.execute(query)
        return result.scalars().all()
