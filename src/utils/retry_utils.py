import asyncio
import random
from loguru import logger
from .error_utils import as_error, error_string

DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF_MS = 1000
DEFAULT_BACKOFF_MULTIPLIER = 2


async def sleep_for(ms: int):
    await asyncio.sleep(ms / 1000)


class RetryError(Exception):
    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message)
        self.__cause__ = cause


async def retry(action, max_retries=DEFAULT_MAX_RETRIES, initial_backoff_ms=DEFAULT_INITIAL_BACKOFF_MS):
    attempt = 1
    backoff_ms = initial_backoff_ms
    while attempt <= max_retries:
        try:
            return await action()
        except Exception as e:
            error = as_error(e)
            logger.warning(f"Error in retry attempt {attempt}/{max_retries}: {error_string(error)}")
            attempt += 1
            if attempt > max_retries:
                raise RetryError(f"Failed to execute action after {max_retries} attempts", error) from error

            randomised_backoff_ms = backoff_ms / 2 + random.randint(0, backoff_ms)
            await sleep_for(randomised_backoff_ms)
            backoff_ms *= DEFAULT_BACKOFF_MULTIPLIER

    raise Exception("Unreachable")