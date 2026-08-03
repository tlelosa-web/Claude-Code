import threading
import time


class RateLimiter:
    """Token-bucket limiter: up to `capacity` calls proceed immediately,
    then callers block until tokens refill at `rate` per `period` seconds."""

    def __init__(self, rate: float, period: float = 60.0, capacity: int | None = None):
        self.rate = rate
        self.period = period
        self.capacity = capacity if capacity is not None else rate
        self._tokens = float(self.capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._last_refill = now
            self._tokens = min(self.capacity, self._tokens + elapsed * (self.rate / self.period))

            if self._tokens < 1:
                wait = (1 - self._tokens) * (self.period / self.rate)
                time.sleep(wait)
                self._tokens = 0.0
                self._last_refill = time.monotonic()
            else:
                self._tokens -= 1
