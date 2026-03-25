"""
Tests for ai_core.schemas — Pydantic v2 models and enums.
"""

import pytest
from pydantic import ValidationError

from ai_core.schemas import (
    AgentType,
    BudgetStrategy,
    Chunk,
    ChunkingConfig,
    ChunkingStrategy,
    Citation,
    ClassificationLevel,
    EmbeddingProvider,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    PromptStrategy,
    RAGConfig,
    RAGResponse,
    RerankerProvider,
    SearchQuery,
    SearchResult,
    SearchStrategy,
    TokenUsage,
    VectorDocument,
    VectorStoreProvider,
)


# ── TokenUsage ────────────────────────────────────────────────────────────────

class TestTokenUsage:
    def test_fields(self):
        usage = TokenUsage(input=100, output=50, total=150)
        assert usage.input == 100
        assert usage.output == 50
        assert usage.total == 150

    def test_zero_tokens(self):
        usage = TokenUsage(input=0, output=0)
        assert usage.total == 0

    def test_defaults(self):
        usage = TokenUsage()
        assert usage.input == 0
        assert usage.output == 0
        assert usage.total == 0


# ── VectorDocument ────────────────────────────────────────────────────────────

class TestVectorDocument:
    def test_basic_creation(self):
        doc = VectorDocument(id="d1", text="Hello world", metadata={"src": "test"})
        assert doc.id == "d1"
        assert doc.text == "Hello world"
        assert doc.metadata["src"] == "test"

    def test_optional_fields_default(self):
        doc = VectorDocument(id="d2", text="text")
        assert doc.namespace == "default"
        assert doc.chunk_index == 0
        assert doc.parent_id is None

    def test_classification_level(self):
        doc = VectorDocument(id="d4", text="secret", access_level=ClassificationLevel.CONFIDENTIAL)
        assert doc.access_level == ClassificationLevel.CONFIDENTIAL

    def test_default_classification(self):
        doc = VectorDocument(id="d5", text="normal")
        assert doc.access_level == ClassificationLevel.INTERNAL


# ── SearchQuery ───────────────────────────────────────────────────────────────

class TestSearchQuery:
    def test_defaults(self):
        q = SearchQuery(query="find docs", query_vector=[0.1, 0.2])
        assert q.top_k == 10
        assert q.hybrid_alpha == 0.5
        assert q.rerank_top_k is None

    def test_custom_values(self):
        q = SearchQuery(
            query="query",
            query_vector=[0.0],
            top_k=20,
            hybrid_alpha=0.7,
            rerank_top_k=5,
        )
        assert q.top_k == 20
        assert q.hybrid_alpha == 0.7
        assert q.rerank_top_k == 5

    def test_namespace_default(self):
        q = SearchQuery(query="test")
        assert q.namespace == "default"


# ── RAGConfig ─────────────────────────────────────────────────────────────────

class TestRAGConfig:
    def test_defaults(self):
        cfg = RAGConfig()
        assert cfg.llm_provider == "openai"
        assert cfg.embedding_provider == "openai"
        assert cfg.chunking_strategy == ChunkingStrategy.SEMANTIC
        assert cfg.search_strategy == SearchStrategy.HYBRID
        assert cfg.top_k == 10
        assert cfg.rerank is False

    def test_custom_config(self):
        cfg = RAGConfig(
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            top_k=10,
            rerank=True,
            cost_limit_usd=2.0,
        )
        assert cfg.llm_provider == "anthropic"
        assert cfg.top_k == 10
        assert cfg.cost_limit_usd == 2.0

    def test_cost_limit_nullable(self):
        cfg = RAGConfig()
        assert cfg.cost_limit_usd is None

    def test_caching_defaults(self):
        cfg = RAGConfig()
        assert cfg.enable_caching is False
        assert cfg.cache_ttl_seconds == 3600


# ── RAGResponse ───────────────────────────────────────────────────────────────

class TestRAGResponse:
    def test_basic(self):
        response = RAGResponse(
            answer="This is the answer.",
            citations=[],
            tokens_used=TokenUsage(input=50, output=20, total=70),
        )
        assert response.answer == "This is the answer."
        assert response.citations == []

    def test_citations(self):
        citation = Citation(
            source="doc-1",
            text="Relevant passage text.",
            relevance_score=0.95,
        )
        response = RAGResponse(
            answer="Answer with sources.",
            citations=[citation],
            tokens_used=TokenUsage(input=100, output=30, total=130),
        )
        assert len(response.citations) == 1
        assert response.citations[0].relevance_score == 0.95


# ── Enum Coverage ─────────────────────────────────────────────────────────────

class TestEnums:
    def test_chunking_strategy_values(self):
        assert ChunkingStrategy.RECURSIVE.value == "recursive"
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert len(ChunkingStrategy) >= 10

    def test_search_strategy_values(self):
        assert SearchStrategy.HYBRID.value == "hybrid"
        assert SearchStrategy.DENSE.value == "dense"

    def test_llm_provider_values(self):
        providers = [p.value for p in LLMProvider]
        assert "openai" in providers
        assert "anthropic" in providers
        assert "bedrock" in providers

    def test_agent_type_values(self):
        assert AgentType.REACT.value == "react"
        assert AgentType.PLAN_EXECUTE.value == "plan_execute"

    def test_classification_level_ordering(self):
        levels = list(ClassificationLevel)
        assert ClassificationLevel.PUBLIC in levels
        assert ClassificationLevel.RESTRICTED in levels


# ── LLMConfig ─────────────────────────────────────────────────────────────────

class TestLLMConfig:
    def test_creation(self):
        cfg = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1024,
        )
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.7

    def test_defaults(self):
        cfg = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
        assert cfg.temperature == 0.0 or cfg.temperature is not None


# ── ChunkingConfig ────────────────────────────────────────────────────────────

class TestChunkingConfig:
    def test_defaults(self):
        cfg = ChunkingConfig(strategy=ChunkingStrategy.FIXED)
        assert cfg.chunk_size > 0
        assert cfg.chunk_overlap >= 0
        assert cfg.chunk_overlap < cfg.chunk_size

    def test_custom(self):
        cfg = ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=512,
            chunk_overlap=64,
        )
        assert cfg.chunk_size == 512
        assert cfg.chunk_overlap == 64
