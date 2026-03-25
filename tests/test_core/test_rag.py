"""
Tests for ai_core.rag — RAGPipeline integration (unit-level with mocks).
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_core.rag import RAGPipeline
from ai_core.schemas import (
    ChunkingStrategy,
    PipelineHook,
    RAGConfig,
    RAGResponse,
    SearchStrategy,
    TokenUsage,
    VectorDocument,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def rag_config() -> RAGConfig:
    return RAGConfig(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        embedding_provider="openai",
        vector_store_provider="chroma",
        chunking_strategy=ChunkingStrategy.RECURSIVE,
        search_strategy=SearchStrategy.HYBRID,
        top_k=3,
        rerank=False,
        cost_limit_usd=5.0,
    )


@pytest.fixture
def sample_docs() -> list[str]:
    return [
        f"Document {i}: Sample content about topic {i}."
        for i in range(5)
    ]


@pytest.fixture
def mock_rag_response() -> RAGResponse:
    return RAGResponse(
        answer="This is a generated answer based on the retrieved context.",
        citations=[],
        tokens_used=TokenUsage(input=150, output=50, total=200),
    )


# ── Component Injection ───────────────────────────────────────────────────────

class TestComponentInjection:
    def test_set_store(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        mock_store = MagicMock()
        pipeline.set_store(mock_store)
        assert pipeline._store is mock_store

    def test_set_embedder(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        mock_embedder = MagicMock()
        pipeline.set_embedder(mock_embedder)
        assert pipeline._embedder is mock_embedder

    def test_set_llm(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        mock_llm = MagicMock()
        pipeline.set_llm(mock_llm)
        assert pipeline._llm is mock_llm

    def test_set_reranker(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        mock_reranker = MagicMock()
        pipeline.set_reranker(mock_reranker)
        assert pipeline._reranker is mock_reranker


# ── Hook System ───────────────────────────────────────────────────────────────

class TestPipelineHooks:
    def test_add_pre_retrieval_hook(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        called: list[dict] = []
        pipeline.add_hook(PipelineHook.PRE_RETRIEVAL, lambda ctx: called.append(ctx))
        assert PipelineHook.PRE_RETRIEVAL in pipeline._hooks

    def test_add_post_generation_hook(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        called: list[dict] = []
        pipeline.add_hook(PipelineHook.POST_GENERATION, lambda ctx: called.append(ctx))
        assert PipelineHook.POST_GENERATION in pipeline._hooks

    def test_multiple_hooks_same_stage(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        pipeline.add_hook(PipelineHook.PRE_RETRIEVAL, lambda ctx: None)
        pipeline.add_hook(PipelineHook.PRE_RETRIEVAL, lambda ctx: None)
        assert len(pipeline._hooks[PipelineHook.PRE_RETRIEVAL]) == 2


# ── Ingest ────────────────────────────────────────────────────────────────────

class TestIngest:
    @pytest.mark.asyncio
    async def test_ingest_calls_chunker_and_embedder(self, rag_config, sample_docs):
        pipeline = RAGPipeline(rag_config)

        mock_store = AsyncMock()
        mock_embedder = AsyncMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 1536)
        mock_embedder.embed_documents = AsyncMock(
            return_value=[[0.1] * 1536 for _ in range(len(sample_docs))]
        )

        pipeline.set_store(mock_store)
        pipeline.set_embedder(mock_embedder)

        await pipeline.ingest(sample_docs, namespace="test-ns")

        mock_store.upsert.assert_called()

    @pytest.mark.asyncio
    async def test_batch_ingest(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        mock_store = AsyncMock()
        mock_embedder = AsyncMock()
        mock_embedder.embed = AsyncMock(return_value=[0.0] * 1536)
        mock_embedder.embed_documents = AsyncMock(return_value=[[0.0] * 1536])
        pipeline.set_store(mock_store)
        pipeline.set_embedder(mock_embedder)

        large_docs = [f"Doc {i} content here." for i in range(50)]
        await pipeline.batch_ingest(large_docs, namespace="batch-ns", batch_size=10)
        assert mock_store.upsert.call_count >= 1


# ── Query ─────────────────────────────────────────────────────────────────────

class TestQuery:
    @pytest.mark.asyncio
    async def test_query_returns_rag_response(self, rag_config, mock_rag_response):
        pipeline = RAGPipeline(rag_config)

        mock_store = AsyncMock()
        mock_store.search = AsyncMock(return_value=[
            MagicMock(
                id="doc-1",
                text="Retrieved context about the topic.",
                score=0.92,
                metadata={"source": "test"},
                source="test",
            )
        ])
        mock_embedder = AsyncMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 1536)
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=MagicMock(
            text=mock_rag_response.answer,
            cost=0.001,
            usage=MagicMock(input=150, output=50, total=200),
        ))

        pipeline.set_store(mock_store)
        pipeline.set_embedder(mock_embedder)
        pipeline.set_llm(mock_llm)

        response = await pipeline.query("What is RAG?", namespace="test-ns")

        assert isinstance(response, RAGResponse)
        assert len(response.answer) > 0

    @pytest.mark.asyncio
    async def test_query_includes_sources(self, rag_config):
        pipeline = RAGPipeline(rag_config)

        mock_store = AsyncMock()
        mock_store.search = AsyncMock(return_value=[
            MagicMock(id="src-1", text="Source content.", score=0.88, metadata={"source": "test"}, source="test")
        ])
        mock_embedder = AsyncMock()
        mock_embedder.embed = AsyncMock(return_value=[0.2] * 1536)
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=MagicMock(
            text="Answer citing sources.",
            cost=0.001,
            usage=MagicMock(input=100, output=30, total=130),
        ))

        pipeline.set_store(mock_store)
        pipeline.set_embedder(mock_embedder)
        pipeline.set_llm(mock_llm)

        response = await pipeline.query("Test query", include_sources=True)
        assert hasattr(response, "citations")

    @pytest.mark.asyncio
    async def test_cost_limit_enforcement(self, rag_config):
        config = RAGConfig(
            **{**rag_config.model_dump(), "cost_limit_usd": 0.0}
        )
        pipeline = RAGPipeline(config)
        pipeline._total_cost_usd = 1.0  # already over limit

        # Set up mocks so query can execute
        mock_store = AsyncMock()
        mock_store.search = AsyncMock(return_value=[])
        mock_embedder = AsyncMock()
        mock_embedder.embed = AsyncMock(return_value=[0.0] * 1536)
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=MagicMock(
            text="answer", cost=0.01,
            usage=MagicMock(input=10, output=5, total=15),
        ))
        pipeline.set_store(mock_store)
        pipeline.set_embedder(mock_embedder)
        pipeline.set_llm(mock_llm)

        response = await pipeline.query("Will this be blocked?")
        assert "COST LIMIT EXCEEDED" in response.answer


# ── Streaming ─────────────────────────────────────────────────────────────────

class TestStreaming:
    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self, rag_config):
        pipeline = RAGPipeline(rag_config)

        async def mock_stream(*_, **__):
            for token in ["Hello", " ", "world", "!"]:
                yield token

        mock_store = AsyncMock()
        mock_store.search = AsyncMock(return_value=[])
        mock_embedder = AsyncMock()
        mock_embedder.embed = AsyncMock(return_value=[0.0] * 1536)
        mock_llm = MagicMock()
        mock_llm.stream = mock_stream

        pipeline.set_store(mock_store)
        pipeline.set_embedder(mock_embedder)
        pipeline.set_llm(mock_llm)

        tokens = []
        async for t in pipeline.stream("Stream test"):
            tokens.append(t)

        assert len(tokens) > 0


# ── Cost Tracking ─────────────────────────────────────────────────────────────

class TestCostTracking:
    def test_initial_cost_zero(self, rag_config):
        pipeline = RAGPipeline(rag_config)
        assert pipeline._total_cost_usd == 0.0
        assert pipeline._query_count == 0
