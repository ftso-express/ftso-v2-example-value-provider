import asyncio
import ccxt.pro as ccxtpro
import ccxt
import json
import math
import os
import random
import time
from enum import Enum
from typing import List, Dict, Any, Set
from loguru import logger
from pydantic import BaseModel
from pathlib import Path

from data_feeds.base_feed import BaseDataFeed
from data_feeds.volumes import VolumeStore
from dto.provider_requests import FeedId, FeedValueData, FeedVolumeData
from utils.error_utils import as_error
from utils.retry_utils import retry, sleep_for, RetryError
from injector import singleton

RETRY_BACKOFF_MS = 10_000
LAMBDA = float(os.environ.get("MEDIAN_DECAY", 0.00005))
TRADES_HISTORY_SIZE = int(os.environ.get("TRADES_HISTORY_SIZE", 1000))


class FeedCategory(Enum):
    NONE = 0
    CRYPTO = 1
    FX = 2
    COMMODITY = 3
    STOCK = 4


class FeedConfigSource(BaseModel):
    exchange: str
    symbol: str


class FeedConfig(BaseModel):
    feed: FeedId
    sources: List[FeedConfigSource]


class PriceInfo(BaseModel):
    value: float
    time: int
    exchange: str


class LoadResult(BaseModel):
    exchange_name: str
    result: Any


usdt_to_usd_feed_id = FeedId(category=FeedCategory.CRYPTO.value, name="USDT/USD")


def feeds_equal(a: FeedId, b: FeedId) -> bool:
    return a.category == b.category and a.name == b.name


@singleton
class CcxtFeed(BaseDataFeed):
    def __init__(self):
        self.logger = logger
        self.initialized = False
        self.config: List[FeedConfig] = []
        self.config_by_key: Dict[str, FeedConfig] = {}
        self.exchange_by_name: Dict[str, ccxt.Exchange] = {}
        self.latest_price: Dict[str, Dict[str, PriceInfo]] = {}
        self.volumes: Dict[str, Dict[str, VolumeStore]] = {}
        self.fetch_attempted: Set[str] = set()

    async def start(self):
        self.config = self._load_config()
        exchange_to_symbols: Dict[str, Set[str]] = {}

        for feed in self.config:
            for source in feed.sources:
                symbols = exchange_to_symbols.get(source.exchange, set())
                symbols.add(source.symbol)
                exchange_to_symbols[source.exchange] = symbols

        self.logger.info(f"Connecting to exchanges: {list(exchange_to_symbols.keys())}")
        load_exchanges = []
        self.logger.info(f"Initializing exchanges with trade limit {TRADES_HISTORY_SIZE}")
        for exchange_name in list(exchange_to_symbols.keys()):
            try:
                exchange: ccxt.Exchange = getattr(ccxtpro, exchange_name)({'newUpdates': True})
                exchange.options["tradesLimit"] = TRADES_HISTORY_SIZE
                self.exchange_by_name[exchange_name] = exchange
                load_exchanges.append(
                    (exchange_name, retry(lambda: exchange.load_markets(), 2, RETRY_BACKOFF_MS))
                )
            except Exception as e:
                self.logger.warning(f"Failed to initialize exchange {exchange_name}, ignoring: {e}")
                del exchange_to_symbols[exchange_name]

        self.logger.info("Initializing all exchanges")
        load_results = await asyncio.gather(
            *[self._wrap_load_promise(exchange_name, promise) for exchange_name, promise in load_exchanges]
        )

        for res in load_results:
            if res.result['status'] == "fulfilled":
                self.logger.info(f"Exchange {res.exchange_name} initialized successfully.")
            else:
                self.logger.warning(f"Failed to load markets for {res.exchange_name}: {res.result['reason']}")
                if res.exchange_name in exchange_to_symbols:
                    del exchange_to_symbols[res.exchange_name]

        await self._init_watch_trades(exchange_to_symbols)

        self.initialized = True
        self.logger.info("Initialization done, watching trades...")

    async def _wrap_load_promise(self, exchange_name, promise):
        try:
            result = await promise
            return LoadResult(exchange_name=exchange_name, result={'status': 'fulfilled', 'value': result})
        except Exception as e:
            return LoadResult(exchange_name=exchange_name, result={'status': 'rejected', 'reason': e})

    async def get_values(self, feeds: List[FeedId]) -> List[FeedValueData]:
        return await asyncio.gather(*[self.get_value(feed) for feed in feeds])

    async def get_value(self, feed: FeedId) -> FeedValueData:
        price = await self._get_feed_price(feed)
        return FeedValueData(feed=feed, value=price)

    async def get_volumes(self, feeds: List[FeedId], volume_window: int) -> List[FeedVolumeData]:
        usdt_to_usd = await self._get_feed_price(usdt_to_usd_feed_id)
        results = []

        for feed in feeds:
            vol_map = {}
            vol_by_exchange = self.volumes.get(feed.name)
            if vol_by_exchange:
                for exchange, vol_store in vol_by_exchange.items():
                    vol_map[exchange] = vol_store.get_volume(volume_window)

            if feed.name.endswith("/USD") and usdt_to_usd is not None:
                usdt_name = feed.name.replace("/USD", "/USDT")
                usdt_vol_by_exchange = self.volumes.get(usdt_name)
                if usdt_vol_by_exchange:
                    for exchange, vol_store in usdt_vol_by_exchange.items():
                        base_vol = vol_map.get(exchange, 0)
                        usdt_vol = round(vol_store.get_volume(volume_window) * usdt_to_usd)
                        vol_map[exchange] = base_vol + usdt_vol

            results.append(
                FeedVolumeData(
                    feed=feed,
                    volumes=[{"exchange": ex, "volume": vol} for ex, vol in vol_map.items()],
                )
            )
        return results

    async def _init_watch_trades(self, exchange_to_symbols: Dict[str, Set[str]]):
        for exchange_name, symbols in exchange_to_symbols.items():
            exchange = self.exchange_by_name.get(exchange_name)
            if exchange is None:
                continue

            market_ids = []
            for symbol in symbols:
                if symbol in exchange.markets:
                    market_ids.append(exchange.markets[symbol]["id"])
                else:
                    self.logger.warning(f"Market not found for {symbol} on {exchange_name}")

            asyncio.create_task(self._watch(exchange, list(symbols), exchange_name))

    async def _watch(self, exchange: ccxt.Exchange, symbols: List[str], exchange_name: str):
        self.logger.info(f"Watching trades for {symbols} on exchange {exchange_name}")
        if exchange.has.get("watchTradesForSymbols") and exchange.id != "bybit":
            await self._watch_trades_for_symbols(exchange, symbols)
        elif exchange.has.get("watchTrades"):
            for symbol in symbols:
                asyncio.create_task(self._watch_trades_for_symbol(exchange, symbol))
        else:
            self.logger.warning(f"Exchange {exchange.id} does not support watching trades, polling for trades instead")
            await self._fetch_trades(exchange, symbols, exchange_name)

    async def _fetch_trades(self, exchange: ccxt.Exchange, symbols: List[str], exchange_name: str):
        while True:
            try:
                async def fetch_action():
                    for symbol in symbols:
                        trades = await exchange.fetch_trades(symbol)
                        if trades:
                            trades.sort(key=lambda t: t['timestamp'], reverse=True)
                            latest_trade = trades[0]
                            last_price_time = (self.latest_price.get(latest_trade['symbol'], {}).get(exchange.id, PriceInfo(value=0, time=0, exchange=''))).time
                            if latest_trade['timestamp'] > last_price_time:
                                self._set_price(exchange.id, latest_trade['symbol'], latest_trade['price'], latest_trade['timestamp'])
                        else:
                            self.logger.warning(f"No trades found for {symbol} on {exchange_name}")

                await retry(fetch_action, 5, 2000)
                await sleep_for(1_000)
            except Exception as e:
                error = as_error(e)
                if isinstance(error, RetryError):
                    self.logger.debug(f"Failed to fetch trades after multiple retries for {exchange.id}/{symbols}: {error.__cause__}, will attempt again in 5 minutes")
                    await sleep_for(300_000)
                else:
                    raise error

    async def _watch_trades_for_symbols(self, exchange: ccxt.Exchange, symbols: List[str]):
        since_by_symbol = {}
        while True:
            try:
                trades = await exchange.watch_trades_for_symbols(symbols)
                new_trades = [trade for trade in trades if trade['timestamp'] > since_by_symbol.get(trade['symbol'], 0)]
                new_trades.sort(key=lambda t: t['timestamp'])

                if not new_trades:
                    await sleep_for(1000)
                    continue

                last_trade = new_trades[-1]
                self._set_price(exchange.id, last_trade['symbol'], last_trade['price'], last_trade['timestamp'])
                since_by_symbol[last_trade['symbol']] = last_trade['timestamp']
                self._process_volume(exchange.id, last_trade['symbol'], new_trades)
            except Exception as e:
                self.logger.debug(f"Failed to watch trades for {exchange.id}/{symbols}: {as_error(e)}, will retry")
                await sleep_for(10_000)

    async def _watch_trades_for_symbol(self, exchange: ccxt.Exchange, symbol: str):
        since = None
        while True:
            try:
                trades = await exchange.watch_trades(symbol, since)
                if not trades:
                    await sleep_for(1_000)
                    continue

                trades.sort(key=lambda t: t['timestamp'])
                last_trade = trades[-1]
                self._set_price(exchange.id, last_trade['symbol'], last_trade['price'], last_trade['timestamp'])
                since = last_trade['timestamp'] + 1
                self._process_volume(exchange.id, last_trade['symbol'], trades)
            except Exception as e:
                self.logger.debug(f"Failed to watch trades for {exchange.id}/{symbol}: {as_error(e)}, will retry")
                await sleep_for(5_000 + random.random() * 10_000)

    def _process_volume(self, exchange_id: str, symbol: str, trades: List[Dict]):
        exchange_volumes = self.volumes.setdefault(symbol, {})
        volume_store = exchange_volumes.setdefault(exchange_id, VolumeStore())
        volume_store.process_trades(trades)

    def _set_price(self, exchange_name: str, symbol: str, price: float, timestamp: int = None):
        prices = self.latest_price.setdefault(symbol, {})
        prices[exchange_name] = PriceInfo(
            value=price,
            time=timestamp if timestamp is not None else int(time.time() * 1000),
            exchange=exchange_name,
        )

    async def _get_feed_price(self, feed_id: FeedId) -> float | None:
        key = self._feed_key(feed_id)
        config = self.config_by_key.get(key)
        if not config:
            self.logger.warning(f"No config found for {feed_id}")
            return None

        usdt_to_usd = None

        async def convert_to_usd(symbol: str, exchange: str, price: float) -> float | None:
            nonlocal usdt_to_usd
            if usdt_to_usd is None:
                usdt_to_usd = await self._get_feed_price(usdt_to_usd_feed_id)
            if usdt_to_usd is None:
                self.logger.warning(f"Unable to retrieve USDT to USD conversion rate for {symbol} at {exchange}")
                return None
            return price * usdt_to_usd

        prices = []
        for source in config.sources:
            info = self.latest_price.get(source.symbol, {}).get(source.exchange)
            if not info:
                continue

            price = info.value
            if source.symbol.endswith("USDT"):
                price = await convert_to_usd(source.symbol, source.exchange, price)
            if price is None:
                continue

            prices.append(PriceInfo(value=price, time=info.time, exchange=info.exchange))

        if not prices:
            self.logger.warning(f"No prices found for {feed_id}")
            asyncio.create_task(self._fetch_last_prices(config))
            return None

        self.logger.debug(f"Calculating results for {feed_id}")
        return self._weighted_median(prices)

    async def _fetch_last_prices(self, config: FeedConfig):
        feed_key = self._feed_key(config.feed)
        if feed_key in self.fetch_attempted:
            return
        self.fetch_attempted.add(feed_key)

        for source in config.sources:
            exchange = self.exchange_by_name.get(source.exchange)
            if not exchange or not exchange.markets:
                continue

            market = exchange.markets.get(source.symbol)
            if not market:
                continue

            self.logger.info(f"Fetching last price for {market['id']} on {source.exchange}")
            try:
                ticker = await exchange.fetch_ticker(market['id'])
                if not ticker or 'last' not in ticker or ticker['last'] is None:
                    self.logger.log(f"No last price found for {market['id']} on {source.exchange}")
                    continue
                self._set_price(source.exchange, ticker['symbol'], ticker['last'], ticker['timestamp'])
            except Exception as e:
                self.logger.warning(f"Failed to fetch ticker for {market['id']} on {source.exchange}: {e}")

    def _weighted_median(self, prices: List[PriceInfo]) -> float | None:
        if not prices:
            raise ValueError("Price list cannot be empty.")

        prices.sort(key=lambda p: p.time)
        now = int(time.time() * 1000)

        weights = [math.exp(-LAMBDA * (now - p.time)) for p in prices]
        weight_sum = sum(weights)

        if weight_sum == 0:
            return prices[0].value if prices else None

        normalized_weights = [w / weight_sum for w in weights]

        weighted_prices = sorted(
            [{"price": p.value, "weight": w, "exchange": p.exchange, "staleness": now - p.time} for p, w in zip(prices, normalized_weights)],
            key=lambda x: x["price"]
        )

        self.logger.debug("Weighted prices:")
        for wp in weighted_prices:
            self.logger.debug(f"Price: {wp['price']}, weight: {wp['weight']}, staleness ms: {wp['staleness']}, exchange: {wp['exchange']}")

        cumulative_weight = 0
        for wp in weighted_prices:
            cumulative_weight += wp["weight"]
            if cumulative_weight >= 0.5:
                self.logger.debug(f"Weighted median: {wp['price']}")
                return wp["price"]

        self.logger.warning("Unable to calculate weighted median")
        return None

    def _feed_key(self, feed: FeedId) -> str:
        return f"{feed.category}:{feed.name}"

    def _load_config(self) -> List[FeedConfig]:
        network = os.environ.get("NETWORK", "prod")
        config_file = f"{'test-' if network == 'local-test' else ''}feeds.json"
        config_path = Path("src") / "config" / config_file

        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)

            config = [FeedConfig(**item) for item in config_data]

            if not any(feeds_equal(cfg.feed, usdt_to_usd_feed_id) for cfg in config):
                raise ValueError("Must provide USDT feed sources, as it is used for USD conversion.")

            for cfg in config:
                self.config_by_key[self._feed_key(cfg.feed)] = cfg

            self.logger.info(f"Supported feeds: {[cfg.feed.dict() for cfg in config]}")
            return config
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error parsing JSON config: {e}")
            raise e