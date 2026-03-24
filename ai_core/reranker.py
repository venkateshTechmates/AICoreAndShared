"""
Reranker Module — Re-rank retrieved documents for improved relevance.

Supports: Cohere, BGE, Cross-Encoder, LLM-based reranking.
Follows Strategy pattern (OCP) with a central factory (SRP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai_core.schemas import RerankerProvider, SearchResult


class BaseReranker(ABC):
    """Abstract base for all reranker implementations (LSP-compliant)."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        *,
        top_k: int = 3,
    ) -> list[SearchResult]:
        ...


# ── Implementations ──────────────────────────────────────────────────────────


class CohereReranker(BaseReranker):
    """Cohere Rerank API — production-grade neural reranking."""

    def __init__(self, *, model: str = "rerank-english-v3.0", api_key: str | None = None) -> None:
        import cohere  # type: ignore[import-untyped]

        self._client = cohere.AsyncClientV2(api_key=api_key)
        self._model = model

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        *,
        top_k: int = 3,
    ) -> list[SearchResult]:
        if not results:
            return []
        documents = [r.text for r in results]
        resp = await self._client.rerank(
            model=self._model,
            query=query,
            documents=documents,
            top_n=top_k,
        )
        reranked: list[SearchResult] = []
        for item in resp.results:
            original = results[item.index]
            reranked.append(
                SearchResult(
                    id=original.id,
                    text=original.text,
                    score=item.relevance_score,
                    metadata=original.metadata,
                    source=original.source,
                )
            )
        return reranked


class BGEReranker(BaseReranker):
    """BGE (BAAI General Embedding) cross-encoder reranker — local inference."""

    def __init__(self, *, model: str = "BAAI/bge-reranker-v2-m3") -> None:
        self._model_name = model
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]

            self._model = CrossEncoder(self._model_name)
        return self._model

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        *,
        top_k: int = 3,
    ) -> list[SearchResult]:
        import asyncio

        if not results:
            return []
        model = self._load_model()
        pairs = [(query, r.text) for r in results]
        scores = await asyncio.get_event_loop().run_in_executor(
            None, model.predict, pairs
        )
        scored = sorted(
            zip(scores, results),
            key=lambda x: float(x[0]),
            reverse=True,
        )
        return [
            SearchResult(
                id=r.id,
                text=r.text,
                score=float(s),
                metadata=r.metadata,
                source=r.source,
            )
            for s, r in scored[:top_k]
        ]


class CrossEncoderReranker(BaseReranker):
    """Generic cross-encoder reranker using Sentence Transformers."""

    def __init__(self, *, model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self._model_name = model
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]

            self._model = CrossEncoder(self._model_name)
        return self._model

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        *,
        top_k: int = 3,
    ) -> list[SearchResult]:
        import asyncio

        if not results:
            return []
        model = self._load_model()
        pairs = [(query, r.text) for r in results]
        scores = await asyncio.get_event_loop().run_in_executor(
            None, model.predict, pairs
        )
        scored = sorted(
            zip(scores, results),
            key=lambda x: float(x[0]),
            reverse=True,
        )
        return [
            SearchResult(
                id=r.id,
                text=r.text,
                score=float(s),
                metadata=r.metadata,
                source=r.source,
            )
            for s, r in scored[:top_k]
        ]


class LLMReranker(BaseReranker):
    """LLM-based reranking — uses an LLM to judge relevance of each result."""

    def __init__(self, *, llm: Any = None) -> None:
        self._llm = llm

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        *,
        top_k: int = 3,
    ) -> list[SearchResult]:
        if not results or self._llm is None:
            return results[:top_k]

        import json

        scored: list[tuple[float, SearchResult]] = []
        for r in results:
            prompt = (
                "Rate the relevance of the following document to the query "
                "on a scale of 0.0 to 1.0. Respond with ONLY a JSON object: "
                '{"score": <float>}\n\n'
                f"Query: {query}\n\n"
                f"Document: {r.text[:1000]}"
            )
            resp = await self._llm.generate(prompt)
            try:
                data = json.loads(resp.text)
                score = float(data.get("score", 0.0))
            except (json.JSONDecodeError, ValueError, TypeError):
                score = r.score
            scored.append((score, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            SearchResult(
                id=r.id,
                text=r.text,
                score=s,
                metadata=r.metadata,
                source=r.source,
            )
            for s, r in scored[:top_k]
        ]


# ── Factory ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[RerankerProvider, type[BaseReranker]] = {
    RerankerProvider.COHERE: CohereReranker,
    RerankerProvider.BGE: BGEReranker,
    RerankerProvider.CROSS_ENCODER: CrossEncoderReranker,
    RerankerProvider.LLM_RERANKER: LLMReranker,
}


class RerankerFactory:
    """Create reranker instances by provider name."""

    @staticmethod
    def create(
        provider: str | RerankerProvider,
        **kwargs: Any,
    ) -> BaseReranker:
        prov = RerankerProvider(provider)
        cls = _REGISTRY.get(prov)
        if cls is None:
            raise ValueError(f"Unsupported reranker provider: {prov}")
        return cls(**kwargs)

    @staticmethod
    def register(provider: RerankerProvider, cls: type[BaseReranker]) -> None:
        _REGISTRY[provider] = cls
