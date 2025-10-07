import time
from typing import List, Dict
from loguru import logger

HISTORY_SEC = 3600


class VolumeStore:
    def __init__(self):
        self.logger = logger
        self.volume_sec = [0] * HISTORY_SEC
        self.last_ts: int | None = None

    def process_trades(self, trades: List[Dict]):
        for trade in trades:
            if not trade.get("timestamp"):
                self.logger.warning(f"Trade with missing timestamp: {trade}")
                continue

            if self.last_ts and trade["timestamp"] < self.last_ts:
                self.logger.debug(
                    f"Trade with timestamp {trade['timestamp']} is older than last processed trade {self.last_ts}, skipping. Trade: {trade}"
                )
                continue

            t_sec = self._to_sec(trade["timestamp"])
            last_t_sec = self._to_sec(self.last_ts) if self.last_ts else t_sec

            for t in range(last_t_sec + 1, t_sec + 1):
                self.volume_sec[t % HISTORY_SEC] = 0

            volume = self._calculate_volume(trade)
            self.volume_sec[t_sec % HISTORY_SEC] += volume
            self.last_ts = trade["timestamp"]

    def get_volume(self, window_sec: int) -> float:
        if window_sec > HISTORY_SEC:
            raise ValueError(
                f"Requested volume for {window_sec} seconds, but only have {HISTORY_SEC} seconds of history"
            )
        if not self.last_ts:
            return 0

        start_sec = self._to_sec(int(time.time() * 1000)) - window_sec
        end_sec = self._to_sec(self.last_ts)

        volume = 0
        for t in range(start_sec, end_sec):
            volume += self.volume_sec[t % HISTORY_SEC]

        return volume

    def _calculate_volume(self, trade: Dict) -> float:
        return trade["amount"] * trade["price"]

    def _to_sec(self, ms: int) -> int:
        return ms // 1000