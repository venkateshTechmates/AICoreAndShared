"""Pydantic v2 schemas for the entire AI Core library."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class ChunkingStrategy(str, Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    DOCUMENT_AWARE = "document_aware"
    AGENTIC = "agentic"
    SLIDING_WINDOW = "sliding_window"
    PARAGRAPH = "paragraph"
    CODE_AWARE = "code_aware"
    MARKDOWN = "markdown"


class SearchStrategy(str, Enum):
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"
    MMR = "mmr"
    MULTI_QUERY = "multi_query"
    HYDE = "hyde"
    SELF_QUERY = "self_query"
    PARENT_CHILD = "parent_child"
    CONTEXTUAL_COMPRESSION = "contextual_compression"
    STEP_BACK = "step_back"


class RerankerProvider(str, Enum):
    COHERE = "cohere"
    BGE = "bge"
    CROSS_ENCODER = "cross_encoder"
    LLM_RERANKER = "llm_reranker"


class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    AZURE = "azure"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    BEDROCK = "bedrock"
    VERTEX_AI = "vertex_ai"
    BGE = "bge"
    JINA = "jina"


class PromptStrategy(str, Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    REACT = "react"
    TREE_OF_THOUGHT = "tree_of_thought"
    REFLEXION = "reflexion"
    PROGRAM_OF_THOUGHT = "program_of_thought"
    ROLE = "role"
    META = "meta"
    SKELETON_OF_THOUGHT = "skeleton_of_thought"
    RAG = "rag"
    DIRECTIONAL = "directional"
    SELF_CONSISTENCY = "self_consistency"
    ZERO_SHOT_COT = "zero_shot_cot"
    STEP_BACK = "step_back"


class AgentType(str, Enum):
    REACT = "react"
    PLAN_EXECUTE = "plan_execute"
    REFLEXION = "reflexion"
    FUNCTION_CALL = "function_call"
    STRUCTURED = "structured"
    CUSTOM = "custom"


class MemoryType(str, Enum):
    BUFFER = "buffer"
    SUMMARY = "summary"
    VECTOR = "vector"
    REDIS = "redis"
    POSTGRES = "postgres"
    ENTITY = "entity"


class VectorStoreProvider(str, Enum):
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    CHROMA = "chroma"
    MILVUS = "milvus"
    PGVECTOR = "pgvector"
    REDIS = "redis"
    OPENSEARCH = "opensearch"
    AZURE_AI_SEARCH = "azure_ai_search"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    BEDROCK = "bedrock"
    VERTEX_AI = "vertex_ai"
    GROQ = "groq"
    OLLAMA = "ollama"
    TOGETHER = "together"


class BudgetStrategy(str, Enum):
    TRUNCATE_MIDDLE = "truncate_middle"
    SUMMARIZE = "summarize"
    DROP_OLDEST = "drop_oldest"
    PRIORITY_BASED = "priority_based"


class PipelineHook(str, Enum):
    PRE_RETRIEVAL = "pre_retrieval"
    POST_RETRIEVAL = "post_retrieval"
    PRE_GENERATION = "pre_generation"
    POST_GENERATION = "post_generation"


class ClassificationLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


# ── Core Schemas ─────────────────────────────────────────────────────────────

class TokenUsage(BaseModel):
    input: int = 0
    output: int = 0
    total: int = 0


class Citation(BaseModel):
    source: str
    page: int | None = None
    text: str = ""
    relevance_score: float = 0.0


class SearchResult(BaseModel):
    id: str = ""
    text: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = ""


class VectorDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vector: list[float] = Field(default_factory=list)
    text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    namespace: str = "default"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_uri: str = ""
    chunk_index: int = 0
    parent_id: str | None = None
    hash_digest: str = ""
    language: str = "en"
    access_level: ClassificationLevel = ClassificationLevel.INTERNAL
    retention_until: datetime | None = None
    classification_level: ClassificationLevel = ClassificationLevel.INTERNAL


class SearchQuery(BaseModel):
    query: str
    query_vector: list[float] = Field(default_factory=list)
    top_k: int = 10
    namespace: str = "default"
    filters: dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = True
    include_vectors: bool = False
    score_threshold: float | None = None
    search_strategy: SearchStrategy | None = None
    user_id: str | None = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    min_date: datetime | None = None
    max_date: datetime | None = None
    hybrid_alpha: float = 0.5
    rerank_top_k: int | None = None


class RAGConfig(BaseModel):
    vector_db: VectorStoreProvider = VectorStoreProvider.QDRANT
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4o"
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    search_strategy: SearchStrategy = SearchStrategy.HYBRID
    reranker: str | None = None
    prompt_strategy: PromptStrategy = PromptStrategy.RAG
    temperature: float = 0.1
    max_tokens: int = 4096
    top_k: int = 10
    namespace: str = "default"
    vector_db_config: dict[str, Any] = Field(default_factory=dict)
    reranker_top_k: int = 3
    enable_citation_tracking: bool = True
    enable_contextual_compression: bool = False
    cost_limit_usd: float | None = None
    timeout_seconds: int = 120
    enable_caching: bool = False
    cache_ttl_seconds: int = 3600
    observability_enabled: bool = True
    audit_enabled: bool = True


class RAGResponse(BaseModel):
    answer: str = ""
    sources: list[SearchResult] = Field(default_factory=list)
    tokens_used: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    citations: list[Citation] = Field(default_factory=list)


class ChunkingConfig(BaseModel):
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    chunk_size: int = 512
    chunk_overlap: int = 50
    separators: list[str] = Field(default_factory=lambda: ["\n\n", "\n", ". ", " "])
    threshold: float = 0.75  # semantic chunking similarity threshold


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    index: int = 0
    source: str = ""
    start_char: int = 0
    end_char: int = 0


class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    max_retries: int = 3
    api_key: str | None = None
    base_url: str | None = None


class LLMResponse(BaseModel):
    text: str = ""
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost: float = 0.0
    latency_ms: float = 0.0
    model: str = ""


class EmbeddingConfig(BaseModel):
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    model: str = "text-embedding-3-large"
    dimensions: int = 3072
    batch_size: int = 100
    api_key: str | None = None
    base_url: str | None = None


class PromptTemplate(BaseModel):
    name: str
    version: int = 1
    strategy: PromptStrategy = PromptStrategy.ZERO_SHOT
    system: str = ""
    user_template: str = ""
    examples: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)


class AgentStep(BaseModel):
    thought: str = ""
    action: str = ""
    action_input: dict[str, Any] = Field(default_factory=dict)
    observation: str = ""


class AgentResponse(BaseModel):
    output: str = ""
    steps: list[AgentStep] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tokens_used: TokenUsage = Field(default_factory=TokenUsage)


class EvalMetric(BaseModel):
    name: str
    score: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class EvalReport(BaseModel):
    metrics: list[EvalMetric] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pipeline_config: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, float]:
        return {m.name: m.score for m in self.metrics}


# ── Enterprise Schemas ───────────────────────────────────────────────────────

class ProvenanceMetadata(BaseModel):
    source_id: str = ""
    source_type: str = ""
    source_uri: str = ""
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    hash_digest: str = ""
    transformations: list[str] = Field(default_factory=list)


class CostRecord(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    project: str = ""
    user: str = ""


class ModelVersion(BaseModel):
    model_id: str = ""
    version: int = 1
    stage: str = "staging"  # staging | production | archived
    provider: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentVariant(BaseModel):
    name: str
    model: str
    config: dict[str, Any] = Field(default_factory=dict)
    traffic_percent: float = 50.0


class QuotaConfig(BaseModel):
    daily_tokens: int = 1_000_000
    monthly_cost_usd: float = 10_000.0
    concurrent_queries: int = 100
    tokens_per_minute: int = 100_000
