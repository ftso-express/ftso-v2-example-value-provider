import os
from nest.core import Injectable


@Injectable
class AppService:
    def __init__(self):
        self.app_name = "Pynest App"
        self.app_version = "1.0.0"
        self.feed_type = self._get_feed_type()

    def _get_feed_type(self):

        value_provider_impl = os.getenv("VALUE_PROVIDER_IMPL", "ccxt")

        if value_provider_impl == "fixed":
            data_feed = "FixedFeed"
        elif value_provider_impl == "random":
            data_feed = "RandomFeed"
        else:
            # Since CcxtFeed can be injected, we get it from the injector
            # data_feed = injector.get(CcxtFeed)
            data_feed = "CcxtFeed"

        return data_feed

    def get_app_info(self):
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "feed_type": self.feed_type
        }
