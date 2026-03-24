"""
RAG Engine — End-to-end Retrieval-Augmented Generation pipeline.

Supports: multi-provider vector DBs, 10 search strategies, 10 chunking strategies,
           15 prompt strategies, reranking, streaming, batch ingestion, pipeline hooks,
           cost tracking, caching, and observability integration.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, AsyncIterator, Callable

from ai_core.chunking import ChunkingEngine
from ai_core.embeddings import BaseEmbedding, EmbeddingFactory
from ai_core.llm import BaseLLM, LLMFactory
from ai_core.prompts import PromptEngine
from ai_core.reranker import BaseReranker, RerankerFactory
from ai_core.schemas import (
    ChunkingConfig,
    Citation,
    EmbeddingConfig,
    LLMConfig,
    PipelineHook,
    RAGConfig,
    RAGResponse,
    SearchQuery,
    SearchResult,
    TokenUsage,
    VectorDocument,
)
from ai_core.search import SearchStrategyFactory
from ai_core.vectorstore import BaseVectorStore, VectorStoreFactory


class RAGPipeline:
    """Full RAG pipeline with ingest → chunk → embed → store → search → rerank → generate."""

    def __init__(self, config: RAGConfig) -> None:
        self.config = config
        self._hooks: dict[PipelineHook, list[Callable[..., Any]]] = {h: [] for h in PipelineHook}

        # Lazy-initialised components
        self._store: BaseVectorStore | None = None
        self._embedder: BaseEmbedding | None = None
        self._llm: BaseLLM | None = None
        self._reranker: BaseReranker | None = None

        # Cost tracking
        self._total_cost_usd: float = 0.0
        self._query_count: int = 0

    # ── Component Access ─────────────────────────────────────────────────

    @property
    def store(self) -> BaseVectorStore:
        if self._store is None:
            self._store = VectorStoreFactory.create(
                self.config.vector_db,
                self.config.vector_db_config.get("collection", "default"),
                self.config.vector_db_config,
            )
        return self._store

    @property
    def embedder(self) -> BaseEmbedding:
        if self._embedder is None:
            self._embedder = EmbeddingFactory.create("openai", self.config.embedding_model)
        return self._embedder

    @property
    def llm(self) -> BaseLLM:
        if self._llm is None:
            self._llm = LLMFactory.create("openai", self.config.llm_model)
        return self._llm

    @property
    def reranker(self) -> BaseReranker | None:
        if self._reranker is None and self.config.reranker:
            self._reranker = RerankerFactory.create(self.config.reranker)
        return self._reranker

    def set_store(self, store: BaseVectorStore) -> None:
        self._store = store

    def set_embedder(self, embedder: BaseEmbedding) -> None:
        self._embedder = embedder

    def set_llm(self, llm: BaseLLM) -> None:
        self._llm = llm

    def set_reranker(self, reranker: BaseReranker) -> None:
        self._reranker = reranker

    # ── Hooks ────────────────────────────────────────────────────────────

    def add_hook(self, hook: PipelineHook, fn: Callable[..., Any]) -> None:
        self._hooks[hook].append(fn)

    async def _fire_hooks(self, hook: PipelineHook, data: Any) -> Any:
        for fn in self._hooks[hook]:
            result = fn(data)
            if result is not None:
                data = result
        return data

    # ── Ingest ───────────────────────────────────────────────────────────

    async def ingest(
        self,
        documents: list[str],
        *,
        namespace: str | None = None,
        preprocessing: Callable[[str], str] | None = None,
        metadata_extractor: Callable[[str], dict[str, Any]] | None = None,
    ) -> int:
        """Ingest documents: chunk → embed → upsert."""
        ns = namespace or self.config.namespace
        chunking_config = ChunkingConfig(
            strategy=self.config.chunking_strategy,
        )
        chunker = ChunkingEngine.create(self.config.chunking_strategy, chunking_config)
        all_docs: list[VectorDocument] = []

        for doc_text in documents:
            if preprocessing:
                doc_text = preprocessing(doc_text)

            chunks = chunker.chunk(doc_text)
            texts = [c.text for c in chunks]
            vectors = await self.embedder.embed_batch(texts)
            metadata = metadata_extractor(doc_text) if metadata_extractor else {}

            for chunk, vector in zip(chunks, vectors):
                all_docs.append(
                    VectorDocument(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        text=chunk.text,
                        metadata={**metadata, **chunk.metadata},
                        namespace=ns,
                        chunk_index=chunk.index,
                    )
                )

        return await self.store.upsert(all_docs)

    async def batch_ingest(
        self,
        documents: list[str],
        *,
        batch_size: int = 50,
        namespace: str | None = None,
    ) -> int:
        """Ingest documents in batches."""
        total = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            count = await self.ingest(batch, namespace=namespace)
            total += count
        return total

    # ── Query ────────────────────────────────────────────────────────────

    async def query(
        self,
        query: str,
        *,
        namespace: str | None = None,
        filters: dict[str, Any] | None = None,
        prompt_strategy: str | None = None,
        include_sources: bool = True,
    ) -> RAGResponse:
        """Full RAG query: embed → search → prompt → generate."""
        start = time.perf_counter()
        ns = namespace or self.config.namespace

        # Pre-retrieval hook
        query = await self._fire_hooks(PipelineHook.PRE_RETRIEVAL, query)

        # Embed query
        query_vector = await self.embedder.embed(query)

        # Search
        strategy = SearchStrategyFactory.create(self.config.search_strategy)
        results = await strategy.search(
            query,
            query_vector,
            self.store,
            top_k=self.config.top_k,
            namespace=ns,
            filters=filters,
            embedder=self.embedder,
            llm=self.llm,
        )

        # Post-retrieval hook
        results = await self._fire_hooks(PipelineHook.POST_RETRIEVAL, results)

        # Rerank if configured
        if self.reranker is not None:
            rerank_k = self.config.reranker_top_k
            results = await self.reranker.rerank(query, results, top_k=rerank_k)

        # Build prompt
        context = "\n\n".join(r.text for r in results)
        engine = PromptEngine()
        ps = prompt_strategy or self.config.prompt_strategy
        prompt = engine.build(technique=ps, system="Answer based on the context provided.", query=query, context=context)

        # Pre-generation hook
        prompt = await self._fire_hooks(PipelineHook.PRE_GENERATION, prompt)

        # Generate
        llm_resp = await self.llm.generate(prompt)

        # Post-generation hook
        answer = await self._fire_hooks(PipelineHook.POST_GENERATION, llm_resp.text)

        elapsed = (time.perf_counter() - start) * 1000

        citations = [
            Citation(
                source=r.metadata.get("source", r.source),
                text=r.text[:200],
                relevance_score=r.score,
            )
            for r in results[:5]
        ] if include_sources else []

        # Track cost
        self._total_cost_usd += llm_resp.cost
        self._query_count += 1

        # Cost limit enforcement
        if self.config.cost_limit_usd is not None and self._total_cost_usd > self.config.cost_limit_usd:
            return RAGResponse(
                answer="[COST LIMIT EXCEEDED] Query budget exhausted.",
                tokens_used=TokenUsage(),
                latency_ms=elapsed,
            )

        return RAGResponse(
            answer=answer if isinstance(answer, str) else llm_resp.text,
            sources=results if include_sources else [],
            tokens_used=TokenUsage(
                input=llm_resp.usage.input,
                output=llm_resp.usage.output,
                total=llm_resp.usage.total,
            ),
            latency_ms=elapsed,
            citations=citations,
        )

    # ── Streaming ────────────────────────────────────────────────────────

    async def stream(
        self,
        query: str,
        *,
        namespace: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream the generation response token by token."""
        ns = namespace or self.config.namespace
        query_vector = await self.embedder.embed(query)
        strategy = SearchStrategyFactory.create(self.config.search_strategy)
        results = await strategy.search(
            query, query_vector, self.store, top_k=self.config.top_k, namespace=ns, filters=filters
        )
        context = "\n\n".join(r.text for r in results)
        engine = PromptEngine()
        prompt = engine.build(
            technique=self.config.prompt_strategy,
            system="Answer based on the context provided.",
            query=query,
            context=context,
        )
        async for token in self.llm.stream(prompt):
            yield token

    # ── Multi-query ──────────────────────────────────────────────────────

    async def multi_query(
        self,
        query: str,
        *,
        namespaces: list[str] | None = None,
        merge_strategy: str = "rrf",
    ) -> RAGResponse:
        """Query across multiple namespaces and merge results."""
        nss = namespaces or [self.config.namespace]
        all_results: list[SearchResult] = []
        query_vector = await self.embedder.embed(query)

        for ns in nss:
            strategy = SearchStrategyFactory.create(self.config.search_strategy)
            results = await strategy.search(
                query, query_vector, self.store, top_k=self.config.top_k, namespace=ns
            )
            all_results.extend(results)

        # De-duplicate and sort
        seen: set[str] = set()
        unique: list[SearchResult] = []
        for r in sorted(all_results, key=lambda x: x.score, reverse=True):
            if r.id not in seen:
                seen.add(r.id)
                unique.append(r)
        unique = unique[: self.config.top_k]

        context = "\n\n".join(r.text for r in unique)
        engine = PromptEngine()
        prompt = engine.build(
            technique=self.config.prompt_strategy,
            system="Answer based on the context provided.",
            query=query,
            context=context,
        )
        llm_resp = await self.llm.generate(prompt)

        return RAGResponse(
            answer=llm_resp.text,
            sources=unique,
            tokens_used=TokenUsage(
                input=llm_resp.usage.input,
                output=llm_resp.usage.output,
                total=llm_resp.usage.total,
            ),
        )
