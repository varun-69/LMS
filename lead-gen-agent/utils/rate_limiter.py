"""
Polite rate limiter for web scraping.

Provides:
  - RateLimiter.wait()    — async random sleep between MIN and MAX seconds
  - retry_with_backoff()  — decorator using tenacity for exponential back-off
"""

import asyncio
import random
import logging
import functools
from typing import Callable, TypeVar, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config.settings import settings

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class RateLimiter:
    """
    Simple async rate limiter that inserts a randomised delay between
    requests to avoid triggering anti-scraping measures.
    """

    def __init__(
        self,
        min_delay: float | None = None,
        max_delay: float | None = None,
    ) -> None:
        self.min_delay = min_delay if min_delay is not None else settings.REQUEST_DELAY_MIN
        self.max_delay = max_delay if max_delay is not None else settings.REQUEST_DELAY_MAX

    async def wait(self) -> None:
        """Sleep for a random duration between min_delay and max_delay seconds."""
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug("Rate limiter sleeping for %.2f seconds", delay)
        await asyncio.sleep(delay)

    def wait_sync(self) -> None:
        """Synchronous version of wait() for non-async contexts."""
        import time

        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug("Rate limiter (sync) sleeping for %.2f seconds", delay)
        time.sleep(delay)


def retry_with_backoff(
    max_attempts: int = 4,
    min_wait: float = 2.0,
    max_wait: float = 60.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator factory that wraps a function with exponential back-off retry
    logic via tenacity.

    Args:
        max_attempts: Maximum number of total attempts (including first try).
        min_wait:     Minimum wait in seconds before first retry.
        max_wait:     Maximum wait cap in seconds.
        exceptions:   Tuple of exception types that trigger a retry.

    Returns:
        A decorator that applies tenacity retry logic to the wrapped function.

    Example::

        @retry_with_backoff(max_attempts=3, exceptions=(requests.exceptions.RequestException,))
        def fetch(url: str) -> str:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retryer = retry(
                reraise=True,
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type(exceptions),
                before_sleep=before_sleep_log(logger, logging.WARNING),
            )
            return retryer(func)(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
