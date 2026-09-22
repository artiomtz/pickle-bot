from datetime import datetime, timezone

from backend.config import settings
from backend.utils.logger_utils import logger


class RateLimiter:
    def __init__(
        self,
        max_tokens: int,
        refill_interval_seconds: int,
    ):
        self.max_tokens = max_tokens
        self.refill_interval_seconds = refill_interval_seconds

        self._tokens = max_tokens
        self._last_refill = datetime.now(timezone.utc)

    def _refill(self) -> None:
        now = datetime.now(timezone.utc)
        elapsed = (now - self._last_refill).total_seconds()

        if elapsed <= 0:
            return

        tokens_to_add = int(elapsed // self.refill_interval_seconds)
        if tokens_to_add <= 0:
            return

        self._tokens = min(self.max_tokens, self._tokens + tokens_to_add)
        self._last_refill = now

    def allow(self) -> bool:
        self._refill()

        if self._tokens <= 0:
            logger.warning("Rate limiter: request denied, tokens=%s max_tokens=%s", self._tokens, self.max_tokens)
            return False

        self._tokens -= 1
        logger.info("Rate limiter: request allowed, tokens=%s max_tokens=%s", self._tokens, self.max_tokens)

        return True


rate_limiter = RateLimiter(
    max_tokens=settings.rate_limit_max_tokens,
    refill_interval_seconds=settings.rate_limit_refill_interval_seconds,
)
