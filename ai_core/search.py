"""
Vector Search Strategies — 9 strategies for intelligent retrieval.

Strategies: dense, sparse, hybrid, mmr, multi_query, hyde,
            self_query, parent_child, contextual_compression
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai_core.schemas import SearchQuery, SearchResult, SearchStrategy


class BaseSearchStrategy(ABC):
    """Abstract base for all search strategies."""

    @abstractmethod
    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        ...


class DenseSearch(BaseSearchStrategy):
    """Standard approximate nearest-neighbour search."""

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        sq = SearchQuery(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            filters=filters or {},
        )
        return await store.search(sq)


class SparseSearch(BaseSearchStrategy):
    """BM25 / TF-IDF sparse keyword search."""

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        # Retrieve a broader set via dense, then re-rank by keyword overlap
        sq = SearchQuery(
            query=query,
            query_vector=query_vector,
            top_k=top_k * 3,
            namespace=namespace,
            filters=filters or {},
        )
        candidates = await store.search(sq)
        query_terms = set(query.lower().split())
        scored: list[tuple[float, SearchResult]] = []
        for r in candidates:
            doc_terms = set(r.text.lower().split())
            overlap = len(query_terms & doc_terms)
            bm25_ish = overlap / (overlap + 1.2) if overlap else 0.0
            scored.append((bm25_ish, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]


class HybridSearch(BaseSearchStrategy):
    """Combine dense + sparse with Reciprocal Rank Fusion (RRF)."""

    def __init__(self, alpha: float = 0.5, fusion: str = "rrf") -> None:
        self.alpha = alpha
        self.fusion = fusion

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        dense = DenseSearch()
        sparse = SparseSearch()
        dense_results = await dense.search(
            query, query_vector, store, top_k=top_k * 2, namespace=namespace, filters=filters
        )
        sparse_results = await sparse.search(
            query, query_vector, store, top_k=top_k * 2, namespace=namespace, filters=filters
        )
        return self._fuse(dense_results, sparse_results, top_k)

    def _fuse(
        self,
        dense: list[SearchResult],
        sparse: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        k = 60  # RRF constant
        scores: dict[str, float] = {}
        doc_map: dict[str, SearchResult] = {}

        for rank, r in enumerate(dense):
            scores[r.id] = scores.get(r.id, 0) + self.alpha / (k + rank + 1)
            doc_map[r.id] = r

        for rank, r in enumerate(sparse):
            scores[r.id] = scores.get(r.id, 0) + (1 - self.alpha) / (k + rank + 1)
            if r.id not in doc_map:
                doc_map[r.id] = r

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results: list[SearchResult] = []
        for id_, score in ranked:
            r = doc_map[id_]
            results.append(SearchResult(id=r.id, text=r.text, score=score, metadata=r.metadata))
        return results


class MMRSearch(BaseSearchStrategy):
    """Maximal Marginal Relevance — balance relevance with diversity."""

    def __init__(self, lambda_mult: float = 0.5) -> None:
        self.lambda_mult = lambda_mult

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        # Retrieve more candidates, then apply MMR
        sq = SearchQuery(
            query=query,
            query_vector=query_vector,
            top_k=top_k * 4,
            namespace=namespace,
            filters=filters or {},
        )
        candidates = await store.search(sq)
        if not candidates:
            return []

        selected: list[SearchResult] = [candidates[0]]
        remaining = candidates[1:]

        while len(selected) < top_k and remaining:
            best_score = -1.0
            best_idx = 0
            for i, cand in enumerate(remaining):
                relevance = cand.score
                max_sim = max(
                    self._text_similarity(cand.text, sel.text) for sel in selected
                )
                mmr = self.lambda_mult * relevance - (1 - self.lambda_mult) * max_sim
                if mmr > best_score:
                    best_score = mmr
                    best_idx = i
            selected.append(remaining.pop(best_idx))

        return selected

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        sa, sb = set(a.lower().split()), set(b.lower().split())
        if not (sa | sb):
            return 0.0
        return len(sa & sb) / len(sa | sb)


class MultiQuerySearch(BaseSearchStrategy):
    """Generate multiple query variants via LLM and merge results."""

    def __init__(self, llm: Any = None, num_queries: int = 3) -> None:
        self.llm = llm
        self.num_queries = num_queries

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        embedder: Any = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        queries = [query]
        if self.llm:
            resp = await self.llm.generate(
                f"Generate {self.num_queries} alternative phrasings of this search query. "
                f"Return one per line, no numbering:\n\n{query}"
            )
            variants = [line.strip() for line in resp.text.strip().split("\n") if line.strip()]
            queries.extend(variants[: self.num_queries])

        all_results: dict[str, SearchResult] = {}
        for q in queries:
            vec = query_vector
            if embedder and q != query:
                vec = await embedder.embed(q)
            sq = SearchQuery(
                query=q, query_vector=vec, top_k=top_k, namespace=namespace, filters=filters or {}
            )
            for r in await store.search(sq):
                if r.id not in all_results or r.score > all_results[r.id].score:
                    all_results[r.id] = r

        ranked = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        return ranked[:top_k]


class HyDESearch(BaseSearchStrategy):
    """Hypothetical Document Embedding — generate a hypothetical answer, embed it, then search."""

    def __init__(self, llm: Any = None) -> None:
        self.llm = llm

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        embedder: Any = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        vec = query_vector
        if self.llm and embedder:
            resp = await self.llm.generate(
                f"Write a short paragraph that answers the following question:\n\n{query}"
            )
            vec = await embedder.embed(resp.text)

        sq = SearchQuery(
            query=query, query_vector=vec, top_k=top_k, namespace=namespace, filters=filters or {}
        )
        return await store.search(sq)


class SelfQuerySearch(BaseSearchStrategy):
    """LLM generates structured filters from the natural-language query."""

    def __init__(self, llm: Any = None) -> None:
        self.llm = llm

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        import json

        auto_filters: dict[str, Any] = {}
        if self.llm:
            resp = await self.llm.generate(
                "Extract metadata filters from this query as JSON. "
                f"If none, return {{}}.\n\nQuery: {query}"
            )
            try:
                auto_filters = json.loads(resp.text)
            except json.JSONDecodeError:
                auto_filters = {}

        merged = {**(filters or {}), **auto_filters}
        sq = SearchQuery(
            query=query, query_vector=query_vector, top_k=top_k, namespace=namespace, filters=merged
        )
        return await store.search(sq)


class ParentChildSearch(BaseSearchStrategy):
    """Retrieve child chunks, return parent context."""

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        sq = SearchQuery(
            query=query, query_vector=query_vector, top_k=top_k * 2, namespace=namespace, filters=filters or {}
        )
        children = await store.search(sq)
        # Group by parent_id and return unique parents
        seen_parents: set[str] = set()
        results: list[SearchResult] = []
        for child in children:
            parent_id = child.metadata.get("parent_id", child.id)
            if parent_id not in seen_parents:
                seen_parents.add(parent_id)
                parent_text = child.metadata.get("parent_text", child.text)
                results.append(
                    SearchResult(
                        id=parent_id,
                        text=parent_text,
                        score=child.score,
                        metadata=child.metadata,
                    )
                )
                if len(results) >= top_k:
                    break
        return results


class ContextualCompressionSearch(BaseSearchStrategy):
    """Retrieve, then compress each result to only the relevant portion."""

    def __init__(self, llm: Any = None) -> None:
        self.llm = llm

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        sq = SearchQuery(
            query=query, query_vector=query_vector, top_k=top_k, namespace=namespace, filters=filters or {}
        )
        results = await store.search(sq)
        if not self.llm:
            return results

        compressed: list[SearchResult] = []
        for r in results:
            resp = await self.llm.generate(
                f"Extract ONLY the parts relevant to the query.\n\n"
                f"Query: {query}\n\nDocument:\n{r.text}"
            )
            compressed.append(
                SearchResult(id=r.id, text=resp.text, score=r.score, metadata=r.metadata)
            )
        return compressed


class StepBackSearch(BaseSearchStrategy):
    """Step-Back Prompting — abstract the question before retrieval for reasoning-heavy queries."""

    def __init__(self, llm: Any = None) -> None:
        self.llm = llm

    async def search(
        self,
        query: str,
        query_vector: list[float],
        store: Any,
        *,
        top_k: int = 10,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        embedder: Any = None,
        **kwargs: Any,
    ) -> list[SearchResult]:
        abstract_query = query
        abstract_vector = query_vector

        if self.llm:
            resp = await self.llm.generate(
                "Given the following specific question, generate a more general "
                "'step-back' question that would help retrieve useful background "
                "knowledge. Return ONLY the step-back question.\n\n"
                f"Specific question: {query}"
            )
            abstract_query = resp.text.strip()
            if embedder:
                abstract_vector = await embedder.embed(abstract_query)

        # Search with both original and abstract queries
        original_sq = SearchQuery(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            filters=filters or {},
        )
        abstract_sq = SearchQuery(
            query=abstract_query,
            query_vector=abstract_vector,
            top_k=top_k,
            namespace=namespace,
            filters=filters or {},
        )

        original_results = await store.search(original_sq)
        abstract_results = await store.search(abstract_sq)

        # Merge via simple deduplication + score-based ranking
        seen: set[str] = set()
        merged: list[SearchResult] = []
        for r in sorted(original_results + abstract_results, key=lambda x: x.score, reverse=True):
            if r.id not in seen:
                seen.add(r.id)
                merged.append(r)
        return merged[:top_k]


# ── Factory ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[SearchStrategy, type[BaseSearchStrategy]] = {
    SearchStrategy.DENSE: DenseSearch,
    SearchStrategy.SPARSE: SparseSearch,
    SearchStrategy.HYBRID: HybridSearch,
    SearchStrategy.MMR: MMRSearch,
    SearchStrategy.MULTI_QUERY: MultiQuerySearch,
    SearchStrategy.HYDE: HyDESearch,
    SearchStrategy.SELF_QUERY: SelfQuerySearch,
    SearchStrategy.PARENT_CHILD: ParentChildSearch,
    SearchStrategy.CONTEXTUAL_COMPRESSION: ContextualCompressionSearch,
    SearchStrategy.STEP_BACK: StepBackSearch,
}


class SearchStrategyFactory:
    """Create search strategy instances."""

    @staticmethod
    def create(strategy: str | SearchStrategy, **kwargs: Any) -> BaseSearchStrategy:
        strat = SearchStrategy(strategy)
        cls = _REGISTRY.get(strat)
        if cls is None:
            raise ValueError(f"Unknown search strategy: {strat}")
        return cls(**kwargs) if kwargs else cls()

    @staticmethod
    def register(strategy: SearchStrategy, cls: type[BaseSearchStrategy]) -> None:
        _REGISTRY[strategy] = cls
