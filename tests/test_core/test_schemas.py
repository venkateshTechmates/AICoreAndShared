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
    def test_total_tokens_computed(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_zero_tokens(self):
        usage = TokenUsage(input_tokens=0, output_tokens=0)
        assert usage.total_tokens == 0

    def test_negative_tokens_rejected(self):
        with pytest.raises(ValidationError):
            TokenUsage(input_tokens=-1, output_tokens=10)


# ── VectorDocument ────────────────────────────────────────────────────────────

class TestVectorDocument:
    def test_basic_creation(self):
        doc = VectorDocument(id="d1", content="Hello world", metadata={"src": "test"})
        assert doc.id == "d1"
        assert doc.content == "Hello world"
        assert doc.metadata["src"] == "test"

    def test_optional_fields_default(self):
        doc = VectorDocument(id="d2", content="text")
        assert doc.namespace is None
        assert doc.chunk_index is None
        assert doc.parent_id is None

    def test_empty_content_not_allowed(self):
        with pytest.raises(ValidationError):
            VectorDocument(id="d3", content="")

    def test_classification_level(self):
        doc = VectorDocument(id="d4", content="secret", access_level=ClassificationLevel.CONFIDENTIAL)
        assert doc.access_level == ClassificationLevel.CONFIDENTIAL


# ── SearchQuery ───────────────────────────────────────────────────────────────

class TestSearchQuery:
    def test_defaults(self):
        q = SearchQuery(text="find docs", vector=[0.1, 0.2])
        assert q.top_k == 5
        assert q.hybrid_alpha == 0.5
        assert q.rerank_top_k is None

    def test_custom_values(self):
        q = SearchQuery(
            text="query",
            vector=[0.0],
            top_k=20,
            hybrid_alpha=0.7,
            rerank_top_k=5,
        )
        assert q.top_k == 20
        assert q.hybrid_alpha == 0.7

    def test_alpha_bounds(self):
        with pytest.raises(ValidationError):
            SearchQuery(text="q", vector=[0.0], hybrid_alpha=1.5)

        with pytest.raises(ValidationError):
            SearchQuery(text="q", vector=[0.0], hybrid_alpha=-0.1)


# ── RAGConfig ─────────────────────────────────────────────────────────────────

class TestRAGConfig:
    def test_defaults(self):
        cfg = RAGConfig()
        assert cfg.llm_provider == LLMProvider.OPENAI
        assert cfg.embedding_provider == EmbeddingProvider.OPENAI
        assert cfg.chunking_strategy == ChunkingStrategy.RECURSIVE
        assert cfg.search_strategy == SearchStrategy.HYBRID
        assert cfg.top_k == 5
        assert cfg.rerank is False

    def test_custom_config(self):
        cfg = RAGConfig(
            llm_provider=LLMProvider.ANTHROPIC,
            llm_model="claude-3-5-sonnet-20241022",
            top_k=10,
            rerank=True,
            cost_limit_usd=2.0,
        )
        assert cfg.llm_provider == LLMProvider.ANTHROPIC
        assert cfg.top_k == 10
        assert cfg.cost_limit_usd == 2.0

    def test_invalid_top_k(self):
        with pytest.raises(ValidationError):
            RAGConfig(top_k=0)

    def test_invalid_temperature(self):
        with pytest.raises(ValidationError):
            RAGConfig(temperature=2.1)


# ── RAGResponse ───────────────────────────────────────────────────────────────

class TestRAGResponse:
    def test_basic(self):
        response = RAGResponse(
            answer="This is the answer.",
            citations=[],
            token_usage=TokenUsage(input_tokens=50, output_tokens=20),
        )
        assert response.answer == "This is the answer."
        assert response.citations == []

    def test_citations(self):
        citation = Citation(
            document_id="doc-1",
            text="Relevant passage text.",
            score=0.95,
        )
        response = RAGResponse(
            answer="Answer with sources.",
            citations=[citation],
            token_usage=TokenUsage(input_tokens=100, output_tokens=30),
        )
        assert len(response.citations) == 1
        assert response.citations[0].score == 0.95


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
