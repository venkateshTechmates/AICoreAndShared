"""
Example 05 — Caching & Resilience
===================================
Demonstrates:
- ExactCache: SHA-256 keyed in-memory LRU with TTL
- SemanticCache: cosine similarity cache with embedding lookup
- RedisCache: Redis-backed cache with TTL
- MultiLayerCache: L1 (exact) → L2 (semantic) with backfill
- CircuitBreaker: CLOSED / OPEN / HALF_OPEN state machine
- RateLimiter: sliding-window token bucket
- @retry: exponential backoff decorator (sync + async)
- @with_timeout: asyncio timeout decorator
- JSONFormatter + LogContext: structured logging

Run:
    python examples/05_caching_resilience.py
"""

import asyncio
import time
from unittest.mock import AsyncMock

from ai_shared.cache import ExactCache, MultiLayerCache, SemanticCache
from ai_shared.logging_utils import LogContext, get_logger, log_execution
from ai_shared.observability import metrics
from ai_shared.resilience import CircuitBreaker, RateLimiter, retry, with_timeout

logger = get_logger("example.cache_resilience", json_output=False)


# ── 1. Exact Cache ────────────────────────────────────────────────────────────

def demo_exact_cache() -> None:
    print("\n── 1. Exact Cache (SHA-256 LRU + TTL) ──────────────")

    cache: ExactCache[str] = ExactCache(max_size=100, ttl_seconds=60)

    # Set values
    cache.set("question: what is RAG?", "RAG stands for Retrieval-Augmented Generation…")
    cache.set("question: what is a vector store?", "A vector store indexes high-dimensional embeddings…")

    # Cache hit
    val = cache.get("question: what is RAG?")
    print(f"  HIT  'what is RAG?' → {val[:50]}…")

    # Cache miss
    miss = cache.get("question: what is LangChain?")
    print(f"  MISS 'what is LangChain?' → {miss!r}")

    # Stats
    print(f"  Size: {cache.size()} / {cache._max_size}")

    # TTL expiry simulation
    cache_short: ExactCache[str] = ExactCache(max_size=10, ttl_seconds=0)
    cache_short.set("ephemeral", "gone in a second")
    time.sleep(0.01)
    expired = cache_short.get("ephemeral")
    print(f"  TTL=0 expired entry → {expired!r}")


# ── 2. Semantic Cache ─────────────────────────────────────────────────────────

async def demo_semantic_cache() -> None:
    print("\n── 2. Semantic Cache (cosine similarity) ────────────")

    # Mock embedder: returns a deterministic vector based on text length
    # (In production use a real EmbeddingFactory-created embedder)
    def mock_embed(text: str) -> list[float]:
        """Toy embedding — first 8 dims based on char counts."""
        chars = set(text.lower())
        v = [float(ord(c) % 16) / 16.0 for c in sorted(chars)[:8]]
        while len(v) < 8:
            v.append(0.0)
        # Normalise
        norm = sum(x ** 2 for x in v) ** 0.5 or 1.0
        return [x / norm for x in v]

    class MockEmbedder:
        async def embed(self, text: str) -> list[float]:
            return mock_embed(text)

    embedder = MockEmbedder()
    sem_cache: SemanticCache[str] = SemanticCache(embedder=embedder, threshold=0.90)

    # Store a cached answer
    await sem_cache.set(
        "How does RAG work?",
        "RAG retrieves relevant documents and uses them as LLM context.",
    )

    # Exact match
    result = await sem_cache.get("How does RAG work?")
    print(f"  Exact : {result!r}")

    # Similar query (different wording — may or may not hit depending on embedder)
    result2 = await sem_cache.get("Explain the RAG architecture")
    print(f"  Similar: {result2!r}")

    # Dissimilar query
    result3 = await sem_cache.get("What is the capital of France?")
    print(f"  Unrelated: {result3!r}")


# ── 3. Multi-Layer Cache ──────────────────────────────────────────────────────

async def demo_multi_layer_cache() -> None:
    print("\n── 3. Multi-Layer Cache (L1 exact → L2 semantic) ────")

    def mock_embed(text: str) -> list[float]:
        v = [float(hash(word) % 256) / 256.0 for word in text.split()[:8]]
        while len(v) < 8: v.append(0.0)
        norm = sum(x**2 for x in v)**0.5 or 1.0
        return [x/norm for x in v]

    class MockEmbedder:
        async def embed(self, text: str) -> list[float]:
            return mock_embed(text)

    l1: ExactCache[str] = ExactCache(max_size=50, ttl_seconds=300)
    l2: SemanticCache[str] = SemanticCache(embedder=MockEmbedder(), threshold=0.85)

    ml_cache: MultiLayerCache[str] = MultiLayerCache(layers=[l1, l2])

    # Populate L1
    await ml_cache.set("What is a transformer?", "A transformer is a neural architecture …")
    await ml_cache.set("What is attention?", "Attention is a mechanism that weights tokens …")

    # L1 hit
    r1 = await ml_cache.get("What is a transformer?")
    print(f"  L1 hit: {r1!r}")

    # Miss
    r2 = await ml_cache.get("Explain gradient descent")
    print(f"  Miss  : {r2!r}")

    print(f"  L1 size: {l1.size()}")


# ── 4. Circuit Breaker ────────────────────────────────────────────────────────

async def demo_circuit_breaker() -> None:
    print("\n── 4. Circuit Breaker ───────────────────────────────")

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=2)
    call_count = 0

    async def flaky_llm_call(succeed: bool) -> str:
        nonlocal call_count
        call_count += 1
        if not succeed:
            raise ConnectionError("LLM endpoint unavailable")
        return "Response from LLM"

    # Successes while CLOSED
    for i in range(2):
        result = await breaker.call(flaky_llm_call, succeed=True)
        print(f"  [{breaker.state}] Call {i+1}: {result}")

    # Trigger failures → OPEN
    for i in range(3):
        try:
            await breaker.call(flaky_llm_call, succeed=False)
        except Exception as exc:
            print(f"  [{breaker.state}] Failure {i+1}: {exc}")

    # Circuit is OPEN — further calls short-circuit
    try:
        await breaker.call(flaky_llm_call, succeed=True)
    except Exception as exc:
        print(f"  [{breaker.state}] Blocked: {exc}")

    # Wait for recovery window, then HALF_OPEN trial
    print(f"  Waiting {breaker._recovery_timeout}s for recovery …")
    await asyncio.sleep(breaker._recovery_timeout + 0.1)

    result = await breaker.call(flaky_llm_call, succeed=True)
    print(f"  [{breaker.state}] Recovered: {result}")

    metrics.increment("circuit_breaker_trips")


# ── 5. Rate Limiter ───────────────────────────────────────────────────────────

async def demo_rate_limiter() -> None:
    print("\n── 5. Rate Limiter (sliding window) ─────────────────")

    # Allow 5 requests per second
    limiter = RateLimiter(requests_per_second=5)

    start = time.monotonic()
    granted = 0
    denied = 0

    for i in range(12):
        if limiter.acquire():
            granted += 1
        else:
            denied += 1

    elapsed = time.monotonic() - start
    print(f"  12 attempts in {elapsed:.3f}s → {granted} granted, {denied} denied")

    # Async rate-limited function
    @limiter.rate_limit()
    async def call_api(n: int) -> str:
        return f"API response #{n}"

    results = await asyncio.gather(*[call_api(i) for i in range(4)], return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            print(f"  Rate limited: {r}")
        else:
            print(f"  Success: {r}")


# ── 6. Retry Decorator ───────────────────────────────────────────────────────

async def demo_retry() -> None:
    print("\n── 6. Retry with Exponential Backoff ────────────────")

    attempt_log: list[float] = []

    @retry(max_attempts=4, base_delay=0.05, backoff="exponential", jitter=False)
    async def unstable_embed(text: str) -> list[float]:
        attempt_log.append(time.monotonic())
        if len(attempt_log) < 3:
            raise TimeoutError(f"Embed service timeout (attempt {len(attempt_log)})")
        return [0.1, 0.2, 0.3]

    start = time.monotonic()
    result = await unstable_embed("test embedding")
    total = time.monotonic() - start

    print(f"  Succeeded on attempt {len(attempt_log)}")
    print(f"  Total elapsed: {total:.3f}s")
    delays = [attempt_log[i] - attempt_log[i-1] for i in range(1, len(attempt_log))]
    for i, d in enumerate(delays, 1):
        print(f"  Delay {i}: {d:.3f}s")

    print(f"  Final result: {result}")


# ── 7. Timeout Decorator ─────────────────────────────────────────────────────

async def demo_timeout() -> None:
    print("\n── 7. Timeout Decorator ─────────────────────────────")

    @with_timeout(seconds=0.2)
    async def slow_operation(duration: float) -> str:
        await asyncio.sleep(duration)
        return "done"

    # Should succeed
    try:
        result = await slow_operation(0.05)
        print(f"  Fast (0.05s): {result}")
    except asyncio.TimeoutError:
        print("  Fast (0.05s): TIMED OUT (unexpected)")

    # Should time out
    try:
        result = await slow_operation(1.0)
        print(f"  Slow (1.0s): {result}")
    except asyncio.TimeoutError:
        print("  Slow (1.0s): TIMED OUT (expected ✓)")


# ── 8. Structured Logging ─────────────────────────────────────────────────────

async def demo_logging() -> None:
    print("\n── 8. Structured Logging ────────────────────────────")

    @log_execution(logger=logger, level="INFO")
    async def process_query(query: str, namespace: str) -> str:
        await asyncio.sleep(0.01)
        return f"Answer for: {query}"

    async with LogContext(logger, user_id="alice", request_id="req-abc123"):
        result = await process_query("What is RAG?", namespace="docs")
        logger.info("processed", extra={"result_length": len(result)})

    logger.info("Context cleared")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    demo_exact_cache()
    await demo_semantic_cache()
    await demo_multi_layer_cache()
    await demo_circuit_breaker()
    await demo_rate_limiter()
    await demo_retry()
    await demo_timeout()
    await demo_logging()
    print("\nAll caching & resilience demos completed.")


if __name__ == "__main__":
    asyncio.run(main())
