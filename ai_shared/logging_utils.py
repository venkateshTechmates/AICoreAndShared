"""
Structured Logging — context-aware, JSON-structured logging utilities.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any


# Context variable for request/trace information
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


# ── JSON formatter ───────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Outputs log records as JSON lines."""

    def __init__(self, *, include_extras: bool = True) -> None:
        super().__init__()
        self.include_extras = include_extras

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }
        # Merge context variables
        ctx = _log_context.get()
        if ctx:
            entry["context"] = ctx
        # Extra fields
        if self.include_extras:
            for key in ("trace_id", "span_id", "user_id", "request_id", "module_name", "duration_ms"):
                val = getattr(record, key, None)
                if val is not None:
                    entry[key] = val
        return json.dumps(entry, default=str)


# ── Context manager ──────────────────────────────────────────────────────────

class LogContext:
    """Context manager that injects fields into all log records within its scope."""

    def __init__(self, **fields: Any) -> None:
        self.fields = fields
        self._token: Any = None

    def __enter__(self) -> LogContext:
        current = _log_context.get()
        merged = {**current, **self.fields}
        self._token = _log_context.set(merged)
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._token is not None:
            _log_context.reset(self._token)


# ── Logger factory ───────────────────────────────────────────────────────────

def get_logger(
    name: str,
    *,
    level: int = logging.INFO,
    json_output: bool = True,
    stream: Any = None,
) -> logging.Logger:
    """Create a pre-configured structured logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler(stream or sys.stdout)

    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    logger.addHandler(handler)
    logger.propagate = False
    return logger


# ── Timed logging decorator ─────────────────────────────────────────────────

def log_execution(logger: logging.Logger | None = None, *, level: int = logging.INFO) -> Any:
    """Decorator that logs function entry, exit, and duration."""
    import functools

    def decorator(fn: Any) -> Any:
        log = logger or get_logger(fn.__module__)

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            log.log(level, f"Entering {fn.__qualname__}")
            try:
                result = await fn(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                log.log(level, f"Exiting {fn.__qualname__} (%.1f ms)", duration)
                return result
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                log.exception(f"Failed {fn.__qualname__} after %.1f ms: {exc}", duration)
                raise

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            log.log(level, f"Entering {fn.__qualname__}")
            try:
                result = fn(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                log.log(level, f"Exiting {fn.__qualname__} (%.1f ms)", duration)
                return result
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                log.exception(f"Failed {fn.__qualname__} after %.1f ms: {exc}", duration)
                raise

        import asyncio

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    return decorator
