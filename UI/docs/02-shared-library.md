# Shared Library Components — Complete Reference

**Package:** `ai-core-lib`  
**Module:** `ai_core.shared`  
**Used by:** All core modules

---

## 1. Configuration Management (`ai_core.config`)

Hierarchical configuration with multiple sources and override precedence.

### Configuration Sources

```python
from ai_core.config import LibConfig

# ── From environment variables / .env file ──
config = LibConfig.from_env()

# ── From YAML ──
config = LibConfig.from_yaml("ai-core.yml")

# ── From HashiCorp Vault ──
config = LibConfig.from_vault("kv/ai-core")

# ── From AWS Secrets Manager ──
config = LibConfig.from_aws_secrets("ai-core/production")

# ── Runtime override ──
config = LibConfig.from_env().override(
    llm_model="gpt-4-turbo",
    temperature=0.2,
)
```

### Override Precedence

```
defaults → yaml file → .env file → environment variables → runtime overrides
(lowest)                                                    (highest)
```

### Complete YAML Configuration

```yaml
# ai-core.yml — Full enterprise configuration

llm:
  default_provider: openai
  default_model: gpt-4o
  fallback_model: gpt-4-turbo
  max_retries: 3
  timeout_seconds: 60
  rate_limit_rpm: 500
  temperature: 0.1

embedding:
  provider: openai
  model: text-embedding-3-large
  dimensions: 3072
  batch_size: 512

vector_store:
  provider: qdrant
  url: ${QDRANT_URL}
  api_key: ${QDRANT_API_KEY}
  default_collection: enterprise_kb
  prefer_grpc: true

rag:
  chunking_strategy: semantic
  search_strategy: hybrid
  reranker: cohere
  top_k: 10
  top_k_after_rerank: 3
  citation_tracking: true
  streaming: true
  contextual_compression: true
  max_context_tokens: 8000

agents:
  default_type: react
  max_iterations: 10
  default_memory: vector
  verbose: false

observability:
  langsmith_enabled: true
  langfuse_enabled: false
  opentelemetry_endpoint: ${OTEL_ENDPOINT}
  tracing_sample_rate: 1.0
  log_level: INFO

security:
  pii_detection: true
  audit_log_level: full
  content_filtering: true
  data_residency: us-east-1

cache:
  provider: redis
  url: ${REDIS_URL}
  semantic_threshold: 0.97
  ttl_seconds: 3600
  exact_match: true
```

---

## 2. LLM Provider Abstraction (`ai_core.llm`)

### Unified Interface

```python
from ai_core.llm import LLMFactory, LLMConfig

# ── Create LLM client ──
llm = LLMFactory.create(
    provider="openai",
    model="gpt-4o",
    config=LLMConfig(
        temperature=0.1,
        max_tokens=4096,
        max_retries=3,
        timeout=60,
        rate_limit_rpm=500,
        fallback_model="gpt-4-turbo",
    ),
)

# ── Generate ──
response = await llm.generate(prompt="Summarize this document...")
print(response.text)
print(response.usage)              # { input_tokens, output_tokens, total_tokens }
print(response.cost)               # Cost in USD
print(response.latency_ms)

# ── Chat ──
response = await llm.chat(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is RAG?"},
    ]
)

# ── Streaming ──
async for chunk in llm.stream("Explain vector databases"):
    print(chunk.text, end="")

# ── Structured Output ──
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    confidence: float
    key_points: list[str]

result = await llm.generate_structured(
    prompt="Analyze this review: ...",
    output_schema=Analysis,
)
print(result.sentiment)            # "positive"
print(result.confidence)           # 0.95
```

### Provider Matrix

| Provider | Models | Streaming | Structured | Function Calling | Batch |
|---|---|:---:|:---:|:---:|:---:|
| **OpenAI** | GPT-4o, GPT-4 Turbo, o1, o3, GPT-4o-mini | ✅ | ✅ | ✅ | ✅ |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus, Haiku | ✅ | ✅ | ✅ | ✅ |
| **Azure OpenAI** | All Azure-deployed models | ✅ | ✅ | ✅ | ✅ |
| **AWS Bedrock** | Claude, Llama 3, Titan, Mistral | ✅ | ✅ | ✅ | ✅ |
| **Google Vertex AI** | Gemini 2.0 Pro/Flash, Gemini 1.5 | ✅ | ✅ | ✅ | ✅ |
| **Groq** | Llama 3, Mixtral (fast inference) | ✅ | ✅ | ✅ | ❌ |
| **Ollama** | Any locally hosted model | ✅ | ◐ | ◐ | ❌ |
| **Together AI** | Open source models | ✅ | ✅ | ✅ | ✅ |

---

## 3. Embedding Abstraction (`ai_core.embeddings`)

```python
from ai_core.embeddings import EmbeddingFactory, EmbeddingConfig

embedder = EmbeddingFactory.create(
    provider="openai",
    model="text-embedding-3-large",
    config=EmbeddingConfig(
        dimensions=3072,
        batch_size=512,
        normalize=True,
        retry_on_rate_limit=True,
    ),
)

# ── Single text ──
vector = await embedder.embed("Hello world")

# ── Batch ──
vectors = await embedder.embed_batch(
    texts=["Hello world", "AI is transforming industries"],
    show_progress=True,
)

# ── With metadata ──
results = await embedder.embed_documents(
    documents=docs,
    include_metadata=True,
)
```

### Supported Embedding Models

| Provider | Model | Dimensions | Speed | Quality |
|---|---|---|---|---|
| OpenAI | text-embedding-3-large | 3072 | Fast | Excellent |
| OpenAI | text-embedding-3-small | 1536 | Very Fast | Good |
| Cohere | embed-english-v3.0 | 1024 | Fast | Excellent |
| Voyage AI | voyage-3-large | 1024 | Fast | Excellent |
| HuggingFace | all-MiniLM-L6-v2 | 384 | Fastest | Good |
| Google | text-embedding-004 | 768 | Fast | Very Good |
| Ollama | nomic-embed-text | 768 | Local | Good |

---

## 4. Memory & State Management (`ai_core.memory`)

### Memory Types

```python
from ai_core.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    VectorMemory,
    RedisMemory,
    PostgresMemory,
    EntityMemory,
)

# ── Buffer Memory (full history) ──
memory = ConversationBufferMemory(
    max_turns=50,
    return_messages=True,
)

# ── Summary Memory (LLM-compressed) ──
memory = ConversationSummaryMemory(
    llm="gpt-4o-mini",
    max_summary_tokens=500,
)

# ── Vector Memory (semantic long-term) ──
memory = VectorMemory(
    store=vector_store,
    namespace="conversation_memory",
    top_k=5,
    relevance_threshold=0.7,
)

# ── Redis Memory (distributed) ──
memory = RedisMemory(
    url="redis://localhost:6379",
    ttl_seconds=3600,
    key_prefix="ai_core:",
)

# ── PostgresMemory (durable) ──
memory = PostgresMemory(
    connection_string="${POSTGRES_URL}",
    table_name="conversation_history",
)

# ── Entity Memory (tracks named entities) ──
memory = EntityMemory(
    llm="gpt-4o-mini",
    entity_store="redis",
)

# ── Usage with agents ──
agent = AgentExecutor.create(
    AgentType.REACT,
    llm=llm,
    tools=[...],
    memory=memory,
)
```

### Memory Comparison

| Type | Persistence | Scalability | Token Cost | Use Case |
|---|---|---|---|---|
| Buffer | In-memory | Low | None | Short conversations |
| Summary | In-memory | Medium | Low | Long conversations |
| Vector | Persistent | High | None | Semantic recall |
| Redis | Persistent | Very High | None | Distributed systems |
| Postgres | Persistent | High | None | Audit + queryable |
| Entity | In-memory | Medium | Low | Entity tracking |

---

## 5. Observability & Tracing (`ai_core.observability`)

### Tracing

```python
from ai_core.observability import Tracer, SpanKind

# ── Decorator-based tracing ──
@Tracer.trace(
    name="rag_pipeline",
    track_tokens=True,
    track_cost=True,
    track_latency=True,
    span_kind=SpanKind.CHAIN,
)
async def run_pipeline(query: str):
    ...

# ── Context manager ──
async with Tracer.span("custom_operation") as span:
    span.set_attribute("query", query)
    result = await some_operation()
    span.set_attribute("result_count", len(result))
```

### Integration Matrix

| Platform | Type | Features |
|---|---|---|
| **LangSmith** | LLM Observability | Prompt traces, evaluations, datasets |
| **Langfuse** | Open Source LLM Obs | Traces, scores, prompt management |
| **Arize Phoenix** | ML Observability | Embeddings, LLM traces, drift |
| **OpenTelemetry** | Standard Tracing | Distributed traces → Jaeger/Datadog |
| **Datadog LLM** | APM + LLM | Full-stack + LLM monitoring |
| **Prometheus** | Metrics | QPS, latency, error rates |

### Metrics Exported

```python
# Auto-exported Prometheus metrics
ai_core_llm_requests_total{provider, model, status}
ai_core_llm_latency_seconds{provider, model, quantile}
ai_core_llm_tokens_total{provider, model, direction}
ai_core_llm_cost_dollars{provider, model}
ai_core_vectorstore_operations_total{provider, operation}
ai_core_rag_queries_total{pipeline, status}
ai_core_cache_hits_total{cache_type}
ai_core_cache_misses_total{cache_type}
```

---

## 6. Token Budget Management (`ai_core.tokens`)

```python
from ai_core.tokens import TokenBudget, BudgetStrategy

budget = TokenBudget(
    model="gpt-4o",
    max_input_tokens=100_000,
    max_output_tokens=4_096,
    context_strategy=BudgetStrategy.TRUNCATE_MIDDLE,
    # Other strategies: SUMMARIZE, DROP_OLDEST, PRIORITY_BASED
)

# ── Fit content within budget ──
safe_prompt = budget.fit(prompt, retrieved_context)

# ── Check remaining budget ──
remaining = budget.remaining_tokens(current_prompt)

# ── Token counting ──
count = budget.count_tokens("Hello world")

# ── Cost estimation ──
cost = budget.estimate_cost(input_tokens=5000, output_tokens=1000)
```

---

## 7. Caching (`ai_core.cache`)

```python
from ai_core.cache import SemanticCache, ExactCache, MultiLayerCache

# ── Semantic Cache — Near-duplicate detection ──
cache = SemanticCache(
    store="redis",
    embedding_model="text-embedding-3-small",
    similarity_threshold=0.97,
    ttl_seconds=3600,
)

# ── Exact Cache — Hash-based ──
cache = ExactCache(
    store="redis",
    ttl_seconds=1800,
)

# ── Multi-Layer Cache ──
cache = MultiLayerCache(
    layers=[
        {"type": "exact", "store": "memory", "ttl": 300},
        {"type": "semantic", "store": "redis", "ttl": 3600},
    ]
)

# ── Usage ──
result = await cache.get(query)
if result is None:
    result = await rag.query(query)
    await cache.set(query, result)
```

---

## 8. Security Utilities (`ai_core.security`)

```python
from ai_core.security import PIIDetector, ContentFilter, InputValidator

# ── PII Detection & Redaction ──
detector = PIIDetector(
    engine="presidio",                  # presidio | regex | llm
    entities=["PERSON", "EMAIL", "PHONE", "SSN", "CREDIT_CARD"],
)

redacted = detector.redact("John Doe's email is john@example.com")
# Result: "[PERSON]'s email is [EMAIL]"

# ── Content Filtering ──
filter = ContentFilter(
    block_categories=["violence", "hate_speech", "sexual_content"],
    check_input=True,
    check_output=True,
)

is_safe = await filter.check(user_input)

# ── Input Validation ──
validator = InputValidator(
    max_length=10000,
    allowed_languages=["en", "es", "fr"],
    block_injection_patterns=True,
)

validated = validator.validate(user_input)
```

---

## 9. Authentication & Authorization (`ai_core.auth`)

```python
from ai_core.auth import AuthManager, RBAC, JWTValidator

# ── API Key Management ──
auth = AuthManager(
    providers=[
        "environment",                   # Environment variables
        "vault",                         # HashiCorp Vault
        "aws_secrets",                   # AWS Secrets Manager
    ],
)

api_key = auth.get_key("openai")

# ── RBAC ──
rbac = RBAC(
    roles={
        "admin": ["*"],
        "data_scientist": ["rag.query", "rag.ingest", "eval.*"],
        "viewer": ["rag.query"],
    }
)

# Check permission
if rbac.has_permission(user, "rag.ingest"):
    await rag.ingest(documents)

# ── JWT Validation ──
validator = JWTValidator(
    issuer="https://auth.company.com",
    audience="ai-core-api",
)

claims = validator.validate(token)
```

---

## 10. Retry & Resilience (`ai_core.resilience`)

```python
from ai_core.resilience import RetryPolicy, CircuitBreaker, RateLimiter

# ── Retry with exponential backoff ──
@RetryPolicy(
    max_retries=3,
    backoff="exponential",
    base_delay=1.0,
    max_delay=30.0,
    retry_on=[RateLimitError, TimeoutError],
)
async def call_llm(prompt: str):
    return await llm.generate(prompt)

# ── Circuit Breaker ──
breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    half_open_max_calls=3,
)

async with breaker:
    result = await external_api.call()

# ── Rate Limiter ──
limiter = RateLimiter(
    requests_per_minute=500,
    tokens_per_minute=100_000,
    strategy="sliding_window",
)

async with limiter:
    response = await llm.generate(prompt)
```

---

## 11. Plugin System (`ai_core.plugins`)

```python
from ai_core.plugins import register_plugin, PluginBase

# ── Register custom vector store ──
@register_plugin("vectorstore")
class MyCustomVectorStore(VectorStoreBase):
    provider = "my_db"
    
    async def upsert(self, documents): ...
    async def search(self, query): ...
    async def delete(self, ids): ...

# ── Register custom embedding provider ──
@register_plugin("embedding")
class MyEmbedding(EmbeddingBase):
    provider = "my_embedding"
    
    async def embed(self, texts): ...

# ── Register custom chunking strategy ──
@register_plugin("chunking")
class MyChunker(ChunkingBase):
    strategy = "my_chunker"
    
    def chunk(self, documents): ...

# ── Register custom LLM provider ──
@register_plugin("llm")
class MyLLM(LLMBase):
    provider = "my_llm"
    
    async def generate(self, prompt): ...
    async def chat(self, messages): ...

# ── Register custom search strategy ──
@register_plugin("search")
class MySearch(SearchStrategyBase):
    strategy = "my_search"
    
    async def search(self, query, store): ...
```

---

## 12. Logging (`ai_core.logging`)

```python
from ai_core.logging import get_logger, configure_logging

# ── Configure ──
configure_logging(
    level="INFO",
    format="json",                      # json | text | structured
    output=["stdout", "file"],
    file_path="logs/ai_core.log",
    rotation="100MB",
    retention="30d",
)

# ── Usage ──
logger = get_logger("rag.pipeline")

logger.info("Pipeline started", query=query, namespace=namespace)
logger.warning("High latency detected", latency_ms=3500)
logger.error("Embedding failed", error=str(e), model=model)
```

---

## 13. Schema Definitions (`ai_core.schemas`)

### Core Schemas (Pydantic v2)

```python
from ai_core.schemas import (
    VectorDocument,
    SearchQuery,
    SearchResult,
    RAGResponse,
    LLMResponse,
    ChunkResult,
    EvalReport,
    AuditEvent,
    CostRecord,
)

# All schemas are Pydantic v2 BaseModel subclasses
# Full type safety, validation, and serialization

class VectorDocument(BaseModel):
    id: str
    vector: list[float]
    text: str
    metadata: dict[str, Any]
    namespace: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_uri: Optional[str] = None
    chunk_index: Optional[int] = None

class RAGResponse(BaseModel):
    answer: str
    sources: list[SearchResult]
    citations: list[Citation]
    tokens_used: TokenUsage
    latency_ms: float
    cost_usd: float
    metadata: dict[str, Any] = {}
```
