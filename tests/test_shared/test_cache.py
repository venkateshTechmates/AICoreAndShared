"""
Tests for ai_shared.cache — ExactCache, SemanticCache, MultiLayerCache.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from ai_shared.cache import ExactCache, MultiLayerCache, SemanticCache


# ── ExactCache ────────────────────────────────────────────────────────────────

class TestExactCache:
    def test_set_and_get(self):
        cache: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        cache.set("hello", "world")
        assert cache.get("hello") == "world"

    def test_miss_returns_none(self):
        cache: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        cache: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=0)
        cache.set("key", "value")
        time.sleep(0.01)
        assert cache.get("key") is None

    def test_lru_eviction(self):
        cache: ExactCache[str] = ExactCache(max_size=3, ttl_seconds=3600)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.set("c", "3")
        # Access 'a' to make it recently used
        cache.get("a")
        # Insert 'd' — should evict 'b' (least recently used)
        cache.set("d", "4")
        assert cache.get("a") == "1"
        assert cache.get("d") == "4"
        # 'b' should be evicted
        assert cache.get("b") is None

    def test_overwrite_existing_key(self):
        cache: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        cache.set("key", "old")
        cache.set("key", "new")
        assert cache.get("key") == "new"

    def test_size(self):
        cache: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        assert cache.size() == 0
        cache.set("a", "1")
        cache.set("b", "2")
        assert cache.size() == 2

    def test_different_value_types(self):
        cache_int: ExactCache[int] = ExactCache(max_size=10, ttl_seconds=60)
        cache_int.set("count", 42)
        assert cache_int.get("count") == 42

        cache_list: ExactCache[list] = ExactCache(max_size=10, ttl_seconds=60)
        cache_list.set("items", [1, 2, 3])
        assert cache_list.get("items") == [1, 2, 3]

    def test_same_key_hashed_consistently(self):
        cache: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        cache.set("What is RAG?", "RAG is …")
        assert cache.get("What is RAG?") == "RAG is …"


# ── SemanticCache ─────────────────────────────────────────────────────────────

def make_embedder(similarity: float = 1.0):
    """Return a mock embedder whose embed always returns a fixed vector."""
    mock = AsyncMock()
    mock.embed = AsyncMock(return_value=[similarity, 0.0, 0.0])
    return mock


class TestSemanticCache:
    @pytest.mark.asyncio
    async def test_exact_match_hit(self):
        embedder = make_embedder(1.0)
        cache: SemanticCache[str] = SemanticCache(embedder=embedder, threshold=0.9)
        await cache.set("What is RAG?", "RAG is retrieval-augmented generation.")
        result = await cache.get("What is RAG?")
        assert result == "RAG is retrieval-augmented generation."

    @pytest.mark.asyncio
    async def test_miss_returns_none(self):
        embedder = make_embedder(0.0)
        cache: SemanticCache[str] = SemanticCache(embedder=embedder, threshold=0.9)
        result = await cache.get("What is LLM?")
        assert result is None

    @pytest.mark.asyncio
    async def test_below_threshold_miss(self):
        """Embedder returning vectors for two different directions → should miss."""
        call_count = 0

        async def embed(text: str) -> list[float]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [1.0, 0.0, 0.0]   # stored vector
            return [0.0, 1.0, 0.0]        # query vector — orthogonal → cosine = 0

        mock = AsyncMock()
        mock.embed = embed
        cache: SemanticCache[str] = SemanticCache(embedder=mock, threshold=0.9)
        await cache.set("query A", "Answer A")
        result = await cache.get("query B")
        assert result is None


# ── MultiLayerCache ───────────────────────────────────────────────────────────

class TestMultiLayerCache:
    @pytest.mark.asyncio
    async def test_l1_hit(self):
        l1: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        ml: MultiLayerCache[str] = MultiLayerCache(layers=[l1])

        await ml.set("hello", "world")
        result = await ml.get("hello")
        assert result == "world"

    @pytest.mark.asyncio
    async def test_backfill_on_l2_hit(self):
        """If L1 misses but L2 hits, result should be backfilled into L1."""
        l1: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=0)   # TTL=0 so L1 miss
        l2: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=3600)

        ml: MultiLayerCache[str] = MultiLayerCache(layers=[l1, l2])

        # Populate L2 directly
        l2.set("question", "answer")

        # L1 should miss (TTL expired or not set), L2 should return and backfill
        result = await ml.get("question")
        assert result == "answer"

    @pytest.mark.asyncio
    async def test_full_miss_returns_none(self):
        l1: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        l2: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        ml: MultiLayerCache[str] = MultiLayerCache(layers=[l1, l2])

        result = await ml.get("nobody stored this")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_populates_all_layers(self):
        l1: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        l2: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=60)
        ml: MultiLayerCache[str] = MultiLayerCache(layers=[l1, l2])

        await ml.set("key", "value")
        assert l1.get("key") == "value"
        assert l2.get("key") == "value"

    @pytest.mark.asyncio
    async def test_single_layer(self):
        l1: ExactCache[str] = ExactCache(max_size=5, ttl_seconds=60)
        ml: MultiLayerCache[str] = MultiLayerCache(layers=[l1])
        await ml.set("x", "y")
        assert await ml.get("x") == "y"
