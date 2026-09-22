from time import sleep

from backend.services.rate_limiter_service import RateLimiter


def test_rate_limiter_basic():
    rl = RateLimiter(max_tokens=3, refill_interval_seconds=1)

    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False

    sleep(1.1)
    assert rl.allow() is True
