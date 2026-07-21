import pytest

from src.shared.rate_limiter import RateLimiter


class _FakeClock:
    def __init__(self, start: float = 0.0):
        self.now = start

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def __call__(self) -> float:
        return self.now


class TestRateLimiter:
    def test_burst_up_to_capacity_does_not_sleep(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr("src.shared.rate_limiter.time.monotonic", clock)
        sleep_calls = []
        monkeypatch.setattr(
            "src.shared.rate_limiter.time.sleep", lambda s: sleep_calls.append(s)
        )

        limiter = RateLimiter(rate=5, period=60.0, capacity=5)
        for _ in range(5):
            limiter.acquire()

        assert sleep_calls == []

    def test_exhausting_capacity_blocks_and_sleeps(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr("src.shared.rate_limiter.time.monotonic", clock)
        sleep_calls = []

        def fake_sleep(seconds):
            sleep_calls.append(seconds)
            clock.advance(seconds)

        monkeypatch.setattr("src.shared.rate_limiter.time.sleep", fake_sleep)

        limiter = RateLimiter(rate=1, period=60.0, capacity=1)
        limiter.acquire()
        limiter.acquire()

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == pytest.approx(60.0, rel=0.01)

    def test_tokens_refill_over_time_avoid_sleep(self, monkeypatch):
        clock = _FakeClock()
        monkeypatch.setattr("src.shared.rate_limiter.time.monotonic", clock)
        sleep_calls = []
        monkeypatch.setattr(
            "src.shared.rate_limiter.time.sleep", lambda s: sleep_calls.append(s)
        )

        limiter = RateLimiter(rate=1, period=60.0, capacity=1)
        limiter.acquire()
        clock.advance(60.0)
        limiter.acquire()

        assert sleep_calls == []
