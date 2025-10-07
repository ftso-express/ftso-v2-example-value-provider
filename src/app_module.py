import os
from nest.core import Module
from injector import Injector, provider, singleton

from app_controller import AppController
from app_service import AppService
from data_feeds.base_feed import BaseDataFeed
from data_feeds.ccxt_provider_service import CcxtFeed
from data_feeds.fixed_feed import FixedFeed
from data_feeds.random_feed import RandomFeed


@singleton
@provider
def app_service_provider(injector: Injector) -> AppService:
    value_provider_impl = os.getenv("VALUE_PROVIDER_IMPL", "ccxt")

    if value_provider_impl == "fixed":
        data_feed = FixedFeed()
    elif value_provider_impl == "random":
        data_feed = RandomFeed()
    else:
        # Since CcxtFeed can be injected, we get it from the injector
        data_feed = injector.get(CcxtFeed)

    return AppService(data_feed=data_feed)


@Module(
    imports=[],
    controllers=[AppController],
    providers=[
        app_service_provider,
        CcxtFeed,
    ],
    exports=[app_service_provider, CcxtFeed],
)
class AppModule:
    pass
