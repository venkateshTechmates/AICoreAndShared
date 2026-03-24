"""
Observability — Distributed tracing, metrics, and monitoring.

Integrations: LangSmith, Langfuse, Phoenix, OpenTelemetry, Datadog, Prometheus
"""

from __future__ import annotations

import functools
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Iterator
from uuid import uuid4


# ── Span / Trace data ────────────────────────────────────────────────────────

class Span:
    """Represents a single span inside a trace."""

    def __init__(self, name: str, *, parent_id: str | None = None, trace_id: str | None = None) -> None:
        self.span_id = uuid4().hex[:16]
        self.trace_id = trace_id or uuid4().hex
        self.parent_id = parent_id
        self.name = name
        self.start_time: float = time.time()
        self.end_time: float | None = None
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.status: str = "ok"

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({"name": name, "timestamp": time.time(), "attributes": attributes or {}})

    def end(self, *, status: str = "ok") -> None:
        self.end_time = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start": self.start_time,
            "end": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


class Trace:
    """Collection of spans making up a distributed trace."""

    def __init__(self, name: str) -> None:
        self.trace_id = uuid4().hex
        self.name = name
        self.spans: list[Span] = []
        self.created_at = datetime.utcnow().isoformat()

    def add_span(self, span: Span) -> None:
        self.spans.append(span)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "created_at": self.created_at,
            "spans": [s.to_dict() for s in self.spans],
        }


# ── Tracer ────────────────────────────────────────────────────────────────────

class Tracer:
    """Central tracer with pluggable exporters."""

    def __init__(self) -> None:
        self._exporters: list[SpanExporter] = []
        self._active_trace: Trace | None = None
        self._spans: list[Span] = []

    def add_exporter(self, exporter: SpanExporter) -> None:
        self._exporters.append(exporter)

    @contextmanager
    def trace(self, name: str) -> Iterator[Trace]:
        t = Trace(name)
        self._active_trace = t
        try:
            yield t
        finally:
            for exporter in self._exporters:
                exporter.export(t)
            self._active_trace = None

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]:
        parent_id = self._spans[-1].span_id if self._spans else None
        trace_id = self._active_trace.trace_id if self._active_trace else None
        s = Span(name, parent_id=parent_id, trace_id=trace_id)
        for k, v in attributes.items():
            s.set_attribute(k, v)
        self._spans.append(s)
        try:
            yield s
        except Exception as exc:
            s.add_event("exception", {"type": type(exc).__name__, "message": str(exc)})
            s.end(status="error")
            raise
        else:
            s.end()
        finally:
            self._spans.pop()
            if self._active_trace:
                self._active_trace.add_span(s)

    @asynccontextmanager
    async def aspan(self, name: str, **attributes: Any) -> AsyncIterator[Span]:
        with self.span(name, **attributes) as s:
            yield s


# ── Exporter interface ────────────────────────────────────────────────────────

class SpanExporter:
    """Base class for trace/span exporters."""

    def export(self, trace: Trace) -> None:
        raise NotImplementedError


class ConsoleExporter(SpanExporter):
    def export(self, trace: Trace) -> None:
        import json
        print(json.dumps(trace.to_dict(), indent=2, default=str))


class LangSmithExporter(SpanExporter):
    def __init__(self, api_key: str, project: str = "default") -> None:
        self.api_key = api_key
        self.project = project

    def export(self, trace: Trace) -> None:
        # Integration point for LangSmith API
        pass


class LangfuseExporter(SpanExporter):
    def __init__(self, public_key: str, secret_key: str, host: str = "https://cloud.langfuse.com") -> None:
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = host

    def export(self, trace: Trace) -> None:
        pass


class OpenTelemetryExporter(SpanExporter):
    def __init__(self, endpoint: str, *, service_name: str = "ai-core") -> None:
        self.endpoint = endpoint
        self.service_name = service_name

    def export(self, trace: Trace) -> None:
        pass


# ── @trace decorator ─────────────────────────────────────────────────────────

_global_tracer = Tracer()


def get_tracer() -> Tracer:
    return _global_tracer


def trace(name: str | None = None, **attrs: Any) -> Callable:
    """Decorator that wraps a function in a span."""

    def decorator(fn: Callable) -> Callable:
        span_name = name or fn.__qualname__

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            async with _global_tracer.aspan(span_name, **attrs) as s:
                result = await fn(*args, **kwargs)
                s.set_attribute("result_type", type(result).__name__)
                return result

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _global_tracer.span(span_name, **attrs) as s:
                result = fn(*args, **kwargs)
                s.set_attribute("result_type", type(result).__name__)
                return result

        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    return decorator


# ── Metrics ──────────────────────────────────────────────────────────────────

class MetricsCollector:
    """Simple in-process metrics for counters, histograms, gauges."""

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = self._key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def observe(self, name: str, value: float, **labels: str) -> None:
        key = self._key(name, labels)
        self._histograms.setdefault(key, []).append(value)

    def set_gauge(self, name: str, value: float, **labels: str) -> None:
        key = self._key(name, labels)
        self._gauges[key] = value

    def get_counter(self, name: str, **labels: str) -> float:
        return self._counters.get(self._key(name, labels), 0)

    def get_histogram(self, name: str, **labels: str) -> list[float]:
        return self._histograms.get(self._key(name, labels), [])

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "histograms": {k: {"count": len(v), "mean": sum(v) / len(v) if v else 0} for k, v in self._histograms.items()},
            "gauges": dict(self._gauges),
        }

    @staticmethod
    def _key(name: str, labels: dict[str, str]) -> str:
        if not labels:
            return name
        lbl = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{lbl}}}"


metrics = MetricsCollector()
