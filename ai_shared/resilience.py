"""
Resilience — Retry policies, circuit breakers, and rate limiters.
"""

from __future__ import annotations

import asyncio
import functools
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, TypeVar

T = TypeVar("T")


# ── Retry Policy ─────────────────────────────────────────────────────────────

class BackoffStrategy(str, Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,)


def retry(config: RetryConfig | None = None) -> Callable:
    """Decorator that retries a function on failure."""
    cfg = config or RetryConfig()

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: BaseException | None = None
            for attempt in range(cfg.max_retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except cfg.retryable_exceptions as exc:
                    last_exc = exc
                    if attempt < cfg.max_retries:
                        delay = _compute_delay(cfg, attempt)
                        await asyncio.sleep(delay)
            raise last_exc  # type: ignore[misc]

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: BaseException | None = None
            for attempt in range(cfg.max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except cfg.retryable_exceptions as exc:
                    last_exc = exc
                    if attempt < cfg.max_retries:
                        delay = _compute_delay(cfg, attempt)
                        time.sleep(delay)
            raise last_exc  # type: ignore[misc]

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    return decorator


def _compute_delay(cfg: RetryConfig, attempt: int) -> float:
    import random

    if cfg.backoff == BackoffStrategy.FIXED:
        delay = cfg.base_delay
    elif cfg.backoff == BackoffStrategy.LINEAR:
        delay = cfg.base_delay * (attempt + 1)
    else:
        delay = cfg.base_delay * (2**attempt)

    delay = min(delay, cfg.max_delay)

    if cfg.jitter:
        delay *= 0.5 + random.random()  # noqa: S311

    return delay


# ── Circuit Breaker ──────────────────────────────────────────────────────────

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Prevents cascading failures by halting calls to failing services."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    async def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        current = self.state
        if current == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit is OPEN, retry after {self.recovery_timeout}s")

        if current == CircuitState.HALF_OPEN and self._half_open_calls >= self.half_open_max_calls:
            raise CircuitOpenError("Circuit half-open, max trial calls reached")

        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        else:
            self._failure_count = 0

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0


class CircuitOpenError(Exception):
    pass


# ── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Token-bucket rate limiter with sliding window."""

    def __init__(
        self,
        *,
        max_calls: int = 60,
        period_seconds: float = 60.0,
    ) -> None:
        self.max_calls = max_calls
        self.period = period_seconds
        self._calls: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.time()
            cutoff = now - self.period
            while self._calls and self._calls[0] < cutoff:
                self._calls.popleft()
            if len(self._calls) >= self.max_calls:
                return False
            self._calls.append(now)
            return True

    async def wait(self) -> None:
        while not await self.acquire():
            await asyncio.sleep(0.1)

    @property
    def remaining(self) -> int:
        now = time.time()
        cutoff = now - self.period
        active = sum(1 for t in self._calls if t >= cutoff)
        return max(0, self.max_calls - active)

    def rate_limit(self) -> Callable:
        """Decorator that rate-limits async function calls."""
        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                await self.wait()
                return await fn(*args, **kwargs)
            return wrapper
        return decorator


# ── Timeout wrapper ──────────────────────────────────────────────────────────

def with_timeout(seconds: float) -> Callable:
    """Decorator that enforces a timeout on async functions."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.wait_for(fn(*args, **kwargs), timeout=seconds)

        return wrapper

    return decorator
