"""
Caching — Semantic, exact-match, and multi-layer caches for LLM/embedding results.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any


class BaseCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...


# ── Exact-match cache ────────────────────────────────────────────────────────

class ExactCache(BaseCache):
    """In-memory LRU cache with TTL, keyed by exact string match."""

    def __init__(self, *, max_size: int = 1000, default_ttl: int = 3600) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: dict[str, _CacheEntry] = {}

    async def get(self, key: str) -> Any | None:
        h = self._hash(key)
        entry = self._store.get(h)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[h]
            return None
        entry.hits += 1
        return entry.value

    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        if len(self._store) >= self.max_size:
            self._evict()
        h = self._hash(key)
        self._store[h] = _CacheEntry(value=value, ttl=ttl or self.default_ttl)

    async def delete(self, key: str) -> None:
        self._store.pop(self._hash(key), None)

    async def clear(self) -> None:
        self._store.clear()

    def _evict(self) -> None:
        # Evict least-recently-used (least hits, then oldest)
        if not self._store:
            return
        victim = min(self._store, key=lambda k: (self._store[k].hits, -self._store[k].created))
        del self._store[victim]

    @staticmethod
    def _hash(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()


# ── Semantic cache ───────────────────────────────────────────────────────────

class SemanticCache(BaseCache):
    """Cache that uses embedding similarity to match semantically equivalent queries."""

    def __init__(
        self,
        embedder: Any,
        *,
        similarity_threshold: float = 0.92,
        max_size: int = 500,
        default_ttl: int = 3600,
    ) -> None:
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._entries: list[_SemanticEntry] = []

    async def get(self, key: str) -> Any | None:
        if not self._entries:
            return None
        query_vec = await self.embedder.embed(key)
        best_score = 0.0
        best_entry: _SemanticEntry | None = None
        for entry in self._entries:
            if entry.is_expired():
                continue
            score = self._cosine(query_vec, entry.vector)
            if score > best_score:
                best_score = score
                best_entry = entry
        if best_entry is not None and best_score >= self.similarity_threshold:
            best_entry.hits += 1
            return best_entry.value
        return None

    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        if len(self._entries) >= self.max_size:
            self._entries = [e for e in self._entries if not e.is_expired()]
            if len(self._entries) >= self.max_size:
                self._entries.sort(key=lambda e: e.hits)
                self._entries.pop(0)
        vector = await self.embedder.embed(key)
        self._entries.append(
            _SemanticEntry(key=key, value=value, vector=vector, ttl=ttl or self.default_ttl)
        )

    async def delete(self, key: str) -> None:
        self._entries = [e for e in self._entries if e.key != key]

    async def clear(self) -> None:
        self._entries.clear()

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)


# ── Redis cache ──────────────────────────────────────────────────────────────

class RedisCache(BaseCache):
    """Distributed cache backed by Redis."""

    def __init__(self, *, url: str = "redis://localhost:6379", prefix: str = "ai_cache", default_ttl: int = 3600) -> None:
        self.url = url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import redis  # type: ignore[import-untyped]
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> Any | None:
        raw = self._get_client().get(f"{self.prefix}:{key}")
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        self._get_client().setex(f"{self.prefix}:{key}", ttl or self.default_ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        self._get_client().delete(f"{self.prefix}:{key}")

    async def clear(self) -> None:
        client = self._get_client()
        keys = client.keys(f"{self.prefix}:*")
        if keys:
            client.delete(*keys)


# ── Multi-layer cache ────────────────────────────────────────────────────────

class MultiLayerCache(BaseCache):
    """Layered cache that checks L1 → L2 → … in order."""

    def __init__(self, layers: list[BaseCache]) -> None:
        if not layers:
            raise ValueError("At least one cache layer is required")
        self.layers = layers

    async def get(self, key: str) -> Any | None:
        for i, layer in enumerate(self.layers):
            value = await layer.get(key)
            if value is not None:
                # Backfill upper layers
                for upper in self.layers[:i]:
                    await upper.set(key, value)
                return value
        return None

    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        for layer in self.layers:
            await layer.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        for layer in self.layers:
            await layer.delete(key)

    async def clear(self) -> None:
        for layer in self.layers:
            await layer.clear()


# ── Internal helpers ─────────────────────────────────────────────────────────

class _CacheEntry:
    __slots__ = ("value", "created", "ttl", "hits")

    def __init__(self, value: Any, ttl: int) -> None:
        self.value = value
        self.created = time.time()
        self.ttl = ttl
        self.hits = 0

    def is_expired(self) -> bool:
        return (time.time() - self.created) > self.ttl


class _SemanticEntry:
    __slots__ = ("key", "value", "vector", "created", "ttl", "hits")

    def __init__(self, key: str, value: Any, vector: list[float], ttl: int) -> None:
        self.key = key
        self.value = value
        self.vector = vector
        self.created = time.time()
        self.ttl = ttl
        self.hits = 0

    def is_expired(self) -> bool:
        return (time.time() - self.created) > self.ttl
