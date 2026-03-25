# UI ↔ Python Codebase Gap Report

**Package**: `ai-enterprise-toolkit` v1.1.0  
**Audit date**: 2026-03  
**Scope**: All 9 UI pages + 5 doc files vs all Python source files  

---

## Critical Cross-Cutting Issues

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 1 | **All `ai_shared` modules import paths are wrong** | `SharedLibraryPage.tsx` (every code block) | Replace every `from ai_core.X import` with `from ai_shared.X import` |
| 2 | **Version shown as `v1.0.0`** | `HomePage.tsx` stats card | Change to `v1.1.0` |
| 3 | **`MCPServer` class does not exist** | `CoreLibraryPage.tsx`, `01-core-library.md` | Replace with `MCPAdapter` from `ai_core.frameworks` |
| 4 | **`AgentPipelineBuilder` class does not exist** | `CoreLibraryPage.tsx`, `01-core-library.md` | Remove — no such class in codebase |
| 5 | **`AICore.from_yaml()` does not exist** | `PlaygroundPage.tsx` code snippet | Replace with `LibConfig.from_yaml(path)` from `ai_core.config` |
| 6 | **`EvalReport.save()` / `.export_html()` do not exist** | UI code blocks referencing `EvalReport` | Remove — `EvalReport` only has `.summary()` |
| 7 | **`ai_shared` modules shown as 12** | `SharedLibraryPage.tsx` | There are 14 modules: auth, cache, compliance, cost, experiments, governance, logging_utils, memory, models, observability, plugins, resilience, security, tokens |

---

## Module-by-Module Gap Report

---

### `ai_core.schemas` — Enums & Models

**Missing from UI entirely:**

```python
# ai_core/schemas.py

class AgentState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"

class PipelineHook(str, Enum):
    PRE_RETRIEVAL = "pre_retrieval"
    POST_RETRIEVAL = "post_retrieval"
    PRE_GENERATION = "pre_generation"
    POST_GENERATION = "post_generation"

class BudgetStrategy(str, Enum):               # schemas.py version (truncation)
    TRUNCATE_MIDDLE = "truncate_middle"
    SUMMARIZE = "summarize"
    DROP_OLDEST = "drop_oldest"
    PRIORITY_BASED = "priority_based"

class ClassificationLevel(str, Enum):          # also in governance.py
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
```

**Missing enum members** (UI shows enum but omits values):

| Enum | Missing values |
|------|----------------|
| `MemoryType` | POSTGRES (UI typically shows 4–5, actual: BUFFER, SUMMARY, VECTOR, REDIS, POSTGRES, ENTITY) |
| `PromptStrategy` | DIRECTIONAL, ZERO_SHOT_COT (15 total; UI shows 12–13) |
| `ChunkingStrategy` | SLIDING_WINDOW, PARAGRAPH (10 total; UI shows 8) |

**Missing Pydantic models** (referenced in code but not documented in UI):

```python
class ProvenanceMetadata(BaseModel):
    source_id: str
    source_type: str
    timestamp: str
    pipeline_id: str
    version: str
    hash_digest: str

class VectorDocument(BaseModel):
    id: str
    vector: list[float]
    text: str
    metadata: dict[str, Any]
    namespace: str
    access_level: ClassificationLevel
    retention_until: str | None
    hash_digest: str
    language: str
    parent_id: str | None

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    cost_usd: float

class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any]
    namespace: str

class Citation(BaseModel):
    doc_id: str
    text: str
    score: float
    source: str
    page: int | None
    metadata: dict[str, Any]
```

---

### `ai_core.config` — `LibConfig`

**Correct import**: `from ai_core.config import LibConfig`  
**UI issue**: referenced as `AICore.from_yaml()` in PlaygroundPage — wrong class name.

```python
class LibConfig(BaseModel):
    # Fields missing from UI:
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072
    vector_db: str = "qdrant"
    vector_db_url: str = "http://localhost:6333"
    vector_db_api_key: str = ""
    vector_db_collection: str = "default"
    chunking_strategy: str = "recursive"
    chunk_size: int = 1024
    chunk_overlap: int = 128
    search_strategy: str = "hybrid"
    search_top_k: int = 10
    cache_enabled: bool = True
    cache_ttl: int = 3600
    log_level: str = "INFO"
    tracing_enabled: bool = False
    tracing_provider: str = "langsmith"
    api_keys: dict[str, str] = {}

    # Factory methods (only from_yaml shown in UI, others missing):
    @classmethod
    def from_env(cls) -> "LibConfig": ...

    @classmethod
    def from_yaml(cls, path: str) -> "LibConfig": ...

    @classmethod
    def from_vault(cls, secret_path: str, *, url: str, token: str) -> "LibConfig": ...

    @classmethod
    def from_aws_secrets(cls, secret_name: str, *, region: str) -> "LibConfig": ...

    # Instance methods (entirely absent from UI):
    def override(self, **kwargs: Any) -> "LibConfig": ...
    def get(self, key: str, default: Any = None) -> Any: ...
```

---

### `ai_core.rag` — `RAGPipeline`

**Missing method signatures** (UI shows the class but omits most params):

```python
class RAGPipeline:
    def __init__(self, config: RAGConfig) -> None: ...

    async def ingest(
        self,
        documents: list[str | dict],
        *,
        namespace: str = "default",
        preprocessing: Callable | None = None,
        metadata_extractor: Callable | None = None,
    ) -> int: ...

    async def batch_ingest(
        self,
        documents: list[str | dict],
        *,
        batch_size: int = 100,
        namespace: str = "default",
    ) -> int: ...

    async def query(
        self,
        query: str,
        *,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
        prompt_strategy: PromptStrategy = PromptStrategy.RAG,
        include_sources: bool = True,
    ) -> RAGResponse: ...

    async def stream(
        self,
        query: str,
        *,
        namespace: str = "default",
        filters: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]: ...

    async def multi_query(
        self,
        query: str,
        *,
        namespaces: list[str],
        merge_strategy: str = "rrf",
    ) -> RAGResponse: ...

    # Hook/setter API — entirely absent from UI:
    def add_hook(self, hook: PipelineHook, fn: Callable) -> None: ...
    def set_store(self, store: BaseVectorStore) -> None: ...
    def set_embedder(self, embedder: BaseEmbedding) -> None: ...
    def set_llm(self, llm: BaseLLM) -> None: ...
    def set_reranker(self, reranker: BaseReranker) -> None: ...
```

---

### `ai_core.vectorstore` — Vector Stores

**Missing stores from UI chunking table** (UI shows all 9 in a grid but no constructors):

```python
class MilvusVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        # config keys: uri, token

class PgVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        # config keys: dsn (e.g. "postgresql://localhost:5432/vectors")

class RedisVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        # config keys: host, port, password, dimensions

class OpenSearchVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        # config keys: hosts, username, password, use_ssl, verify_certs

class AzureAISearchVectorStore(BaseVectorStore):
    def __init__(self, collection: str, config: dict[str, Any]) -> None:
        # config keys: endpoint, api_key (required)
```

**Missing `BaseVectorStore` methods** (UI never documents the base interface):

```python
class BaseVectorStore(ABC):
    async def upsert(self, documents: list[VectorDocument]) -> int: ...
    async def search(self, query: SearchQuery) -> list[SearchResult]: ...
    async def delete(self, ids: list[str]) -> int: ...
    async def delete_namespace(self, namespace: str) -> int: ...
    async def list_namespaces(self) -> list[str]: ...          # missing from UI
    async def collection_stats(self) -> dict[str, Any]: ...   # missing from UI
```

**Missing factory** (entirely absent from UI):

```python
class VectorStoreFactory:
    @staticmethod
    def create(
        provider: str | VectorStoreProvider,
        collection: str,
        config: dict[str, Any] | None = None,
    ) -> BaseVectorStore: ...

    @staticmethod
    def register(provider: VectorStoreProvider, cls: type[BaseVectorStore]) -> None: ...
```

---

### `ai_core.search` — Search Strategies

**Missing chunkers from UI table** (UI shows 8; code has 10):

| Missing class | Module |
|---------------|--------|
| `SlidingWindowChunker` | `ai_core.chunking` |
| `ParagraphChunker` | `ai_core.chunking` |

**Missing search strategy classes** (UI table lists names but no constructors shown):

```python
class ParentChildSearch(BaseSearchStrategy):
    async def search(self, query, query_vector, store, *, top_k, namespace, filters, **kwargs) -> list[SearchResult]: ...

class ContextualCompressionSearch(BaseSearchStrategy):
    def __init__(self, llm: Any = None) -> None: ...
    async def search(self, query, query_vector, store, *, top_k, namespace, filters, **kwargs) -> list[SearchResult]: ...

class StepBackSearch(BaseSearchStrategy):
    def __init__(self, llm: Any = None) -> None: ...
    async def search(self, query, query_vector, store, *, top_k, namespace, filters, embedder, **kwargs) -> list[SearchResult]: ...

class HybridSearch(BaseSearchStrategy):
    def __init__(self, alpha: float = 0.5, fusion: str = "rrf") -> None: ...  # constructor not shown in UI
```

**Missing factory** (entirely absent from UI):

```python
class SearchStrategyFactory:
    @staticmethod
    def create(strategy: str | SearchStrategy, **kwargs: Any) -> BaseSearchStrategy: ...

    @staticmethod
    def register(strategy: SearchStrategy, cls: type[BaseSearchStrategy]) -> None: ...
```

---

### `ai_core.chunking` — Chunkers

**Missing chunker classes**:

```python
class SlidingWindowChunker:
    def __init__(self, config: ChunkingConfig) -> None: ...
    def chunk(self, text: str) -> list[Chunk]: ...

class ParagraphChunker:
    def __init__(self, config: ChunkingConfig) -> None: ...
    def chunk(self, text: str) -> list[Chunk]: ...
```

**Missing async method on `AgenticChunker`** (not shown anywhere in UI):

```python
class AgenticChunker:
    async def chunk_async(
        self,
        text: str,
        llm: BaseLLM,
        *,
        instructions: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]: ...
```

**Missing factory** (UI shows `ChunkingEngine()` but doesn't document static methods):

```python
class ChunkingEngine:
    @staticmethod
    def create(strategy: ChunkingStrategy, config: ChunkingConfig) -> BaseChunker: ...

    @staticmethod
    def chunk(text: str, strategy: ChunkingStrategy, config: ChunkingConfig) -> list[Chunk]: ...
```

---

### `ai_core.prompts` — Prompt Engine

**Missing `PromptStrategy` values** (UI shows 12–13; code has 15):

```python
class PromptStrategy(str, Enum):
    # Present in UI:
    ZERO_SHOT, FEW_SHOT, CHAIN_OF_THOUGHT, REACT, TREE_OF_THOUGHT, REFLEXION,
    PROGRAM_OF_THOUGHT, ROLE, META, SKELETON_OF_THOUGHT, RAG, SELF_CONSISTENCY

    # MISSING from UI:
    DIRECTIONAL = "directional"
    ZERO_SHOT_COT = "zero_shot_cot"
    STEP_BACK = "step_back"
```

**Missing `PromptEngine` signature** (UI shows the class name only):

```python
class PromptEngine:
    def build(
        self,
        *,
        technique: PromptStrategy,
        system: str = "",
        query: str,
        context: str = "",
        examples: list[dict] | None = None,
        role: str = "",
        hint: str = "",
        n: int = 1,
        step_back: str = "",
    ) -> str: ...

    async def execute(self, prompt: str, llm: BaseLLM, *, model: str = "") -> LLMResponse: ...
```

**Missing `PromptRegistry` API** (entirely absent from UI):

```python
class PromptRegistry:
    def register(self, template: PromptTemplate) -> None: ...
    def render(self, name: str, **kwargs: Any) -> str: ...
    def list(self, domain: str | None = None) -> list[PromptTemplate]: ...
    def get_versions(self, name: str) -> list[PromptTemplate]: ...
    def rollback(self, name: str, version: int) -> None: ...
    def clear(self) -> None: ...
```

**Missing `DynamicExampleSelector`** (entirely absent from UI):

```python
class DynamicExampleSelector:
    def __init__(
        self,
        examples: list[dict[str, str]],
        *,
        strategy: str = "semantic",
        k: int = 3,
    ) -> None: ...

    def select(self, query: str) -> list[dict[str, str]]: ...
```

---

### `ai_core.llm` — LLM Providers

**Missing `generate_structured` method** on `BaseLLM` (not documented in UI):

```python
class BaseLLM(ABC):
    async def generate(self, prompt: str, *, model: str = "", temperature: float | None = None, max_tokens: int | None = None) -> LLMResponse: ...
    async def chat(self, messages: list[dict], *, model: str = "", temperature: float | None = None, max_tokens: int | None = None) -> LLMResponse: ...
    async def stream(self, prompt_or_messages: str | list[dict], *, model: str = "") -> AsyncIterator[str]: ...
    async def generate_structured(self, prompt: str, output_schema: type[BaseModel], *, model: str = "") -> BaseModel: ...  # MISSING
```

**Missing `LLMFactory`** (entirely absent from UI):

```python
class LLMFactory:
    @staticmethod
    def create(provider: str | LLMProvider, model: str, *, api_key: str = "", **kwargs: Any) -> BaseLLM: ...

    @staticmethod
    def register(provider: LLMProvider, cls: type[BaseLLM]) -> None: ...
```

---

### `ai_core.embeddings` — Embedding Providers

**Missing methods on `BaseEmbedding`**:

```python
class BaseEmbedding(ABC):
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str], *, batch_size: int = 32) -> list[list[float]]: ...
    async def embed_documents(self, documents: list[VectorDocument]) -> list[VectorDocument]: ...  # MISSING from UI
    async def _embed_batch_impl(self, texts: list[str]) -> list[list[float]]: ...
```

**Missing `EmbeddingFactory`**:

```python
class EmbeddingFactory:
    @staticmethod
    def create(provider: str | EmbeddingProvider, model: str, config: dict[str, Any] | None = None) -> BaseEmbedding: ...

    @staticmethod
    def register(provider: EmbeddingProvider, cls: type[BaseEmbedding]) -> None: ...  # MISSING
```

---

### `ai_core.reranker` — Rerankers

**Missing `RerankerFactory`** (factory exists but `register` method not shown):

```python
class RerankerFactory:
    @staticmethod
    def create(provider: str | RerankerProvider, **kwargs: Any) -> BaseReranker: ...

    @staticmethod
    def register(provider: RerankerProvider, cls: type[BaseReranker]) -> None: ...  # MISSING
```

---

### `ai_core.agents` — Agent System

**Missing `AgentState` enum** (entirely absent from UI):

```python
class AgentState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"
```

**Missing `AgentMessage` dataclass** (MessageBus uses this; not documented):

```python
@dataclass
class AgentMessage:
    id: str
    sender: str
    recipient: str
    content: Any
    msg_type: str
    metadata: dict[str, Any]
    timestamp: float
    parent_id: str | None
```

**Missing `MessageBus` class** (entirely absent from UI):

```python
class MessageBus:
    def publish(self, message: AgentMessage) -> None: ...
    def subscribe(self, agent_name: str, handler: Callable[[AgentMessage], None]) -> None: ...
    def get_history(self, *, sender: str | None = None, recipient: str | None = None) -> list[AgentMessage]: ...
    def get_dead_letters(self) -> list[AgentMessage]: ...
    def clear(self) -> None: ...
```

**Missing `ConflictResolution` dataclass**:

```python
@dataclass
class ConflictResolution:
    strategy: str
    votes: dict[str, Any]
    winner: str
    reason: str
```

**Missing `Tool` and `ToolRegistry`** (UI mentions tools but never documents these classes):

```python
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    async def run(self, **kwargs: Any) -> Any: ...

class ToolRegistry:
    def register(self, tool: Tool) -> None: ...
    def get(self, name: str) -> Tool: ...
    def list_tools(self) -> list[Tool]: ...
    def clear(self) -> None: ...

def tool(name: str, description: str, input_schema: dict[str, Any]) -> Callable:
    """Decorator to create a Tool from a function."""
```

**Missing `BaseAgent` full signature and methods**:

```python
class BaseAgent(ABC):
    def __init__(
        self,
        llm: BaseLLM,
        tools: list[Tool] | None = None,
        *,
        max_iterations: int = 10,
        memory: BaseMemory | None = None,
        verbose: bool = False,
    ) -> None: ...

    async def run(self, query: str, **kwargs: Any) -> AgentResponse: ...
    async def _call_tool(self, name: str, args: dict[str, Any]) -> Any: ...
    def _tool_descriptions(self) -> str: ...
    def _tool_schemas(self) -> list[dict]: ...
    async def _call_llm_with_retry(
        self,
        prompt_or_messages: str | list[dict],
        *,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> LLMResponse: ...
```

**Missing `AgentRole` class** (UI shows MultiAgentSystem but not AgentRole):

```python
class AgentRole:
    def __init__(
        self,
        name: str,
        agent: BaseAgent,
        *,
        role_description: str = "",
        priority: int = 1,
        domain: str = "",
        max_retries: int = 3,
    ) -> None: ...

    state: AgentState
```

**Missing `OrchestrationResult` full fields** (UI shows partial):

```python
@dataclass
class OrchestrationResult:
    output: str
    agent_outputs: dict[str, Any]
    steps: list[AgentStep]
    tokens_used: int
    coordination_mode: CoordinationMode
    conflict_resolution: ConflictResolution | None   # MISSING
    messages_exchanged: int                           # MISSING
    elapsed_seconds: float                            # MISSING
    cost_usd: float                                   # MISSING
    consensus: bool                                   # MISSING
    metadata: dict[str, Any]                          # MISSING

    @property
    def results(self) -> dict[str, Any]: ...
    @property
    def final_answer(self) -> str: ...
    @property
    def cost(self) -> float: ...
```

**Missing `MultiAgentSystem` full constructor**:

```python
class MultiAgentSystem:
    def __init__(
        self,
        agents: list[AgentRole],
        *,
        coordination: str = "sequential",
        mode: CoordinationMode = CoordinationMode.SEQUENTIAL,
        message_bus: MessageBus | None = None,   # MISSING from UI
        max_rounds: int = 5,
        rounds: int = 3,
        cost_limit_usd: float | None = None,     # MISSING from UI
        policy_check: Callable | None = None,    # MISSING from UI
    ) -> None: ...
```

**`AgentPipelineBuilder` does NOT exist** — remove from all UI pages.

---

### `ai_core.frameworks` — Framework Adapters

**`MCPServer` does NOT exist** — the correct class is `MCPAdapter`:

```python
# WRONG (in UI):
server = MCPServer(name="my-server")
server.run(transport="stdio")

# CORRECT (from ai_core.frameworks):
class MCPAdapter(FrameworkAdapter):
    def build_rag_chain(self, config: RAGConfig) -> Any: ...
    def tool(self, name: str) -> Callable: ...        # decorator
    def resource(self, uri: str) -> Callable: ...     # decorator
    def list_tools(self) -> list[dict]: ...
    def list_resources(self) -> list[dict]: ...
    # No run() method exists
```

**Missing adapter methods** (UI shows class names only):

```python
class LangChainAdapter(FrameworkAdapter):
    def build_rag_chain(self, config: RAGConfig) -> Any: ...
    def build_retriever(self, config: RAGConfig) -> Any: ...   # MISSING

class LangGraphAdapter(FrameworkAdapter):
    def build_rag_chain(self, config: RAGConfig) -> Any: ...
    def build_workflow(self, config: RAGConfig) -> Any: ...    # MISSING

class CrewAIAdapter(FrameworkAdapter):
    def build_rag_chain(self, config: RAGConfig) -> Any: ...
    def build_crew(self, config: RAGConfig) -> Any: ...        # MISSING

class AutoGenAdapter(FrameworkAdapter):
    def build_rag_chain(self, config: RAGConfig) -> Any: ...
    def build_group_chat(self, config: RAGConfig) -> Any: ...  # MISSING

# Factory classmethod (absent from UI):
class FrameworkAdapter(ABC):
    @classmethod
    def for_framework(cls, name: str) -> "FrameworkAdapter": ...
```

---

### `ai_core.eval` — Evaluation

**Missing `PipelineEvaluator`** (entirely absent from UI):

```python
class PipelineEvaluator(BaseEvaluator):
    async def evaluate(
        self,
        questions: list[str],
        pipeline: RAGPipeline,
        *,
        ground_truth: list[str] | None = None,
    ) -> EvalReport: ...
```

**Missing `RAGEvaluator` constructor param**:

```python
class RAGEvaluator(BaseEvaluator):
    def __init__(
        self,
        metrics: list[str] | None = None,  # faithfulness, answer_relevancy, context_recall, context_precision, harmfulness, hallucination
        llm: BaseLLM | None = None,         # MISSING from UI; required for LLM-as-judge metrics
    ) -> None: ...
```

**`EvalReport.save()` / `.export_html()` DO NOT EXIST** — `EvalReport` (in `schemas.py`) only has:

```python
class EvalReport(BaseModel):
    metrics: list[EvalMetric]
    questions: list[str]
    documents: list[str]
    report_id: str
    created_at: str
    config: dict[str, Any]

    def summary(self) -> dict[str, Any]: ...  # only method that exists
    # .save() → does NOT exist
    # .export_html() → does NOT exist
```

---

### `ai_core.deployment` — Deployment

**Entire module is absent from UI documentation.** All of the following are undocumented:

```python
# Enums
class RoutingStrategy(str, Enum):
    GEO_LATENCY = "geo_latency"
    USER_LOCATION = "user_location"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"

class ReplicationStrategy(str, Enum):
    ACTIVE_ACTIVE = "active_active"
    ACTIVE_PASSIVE = "active_passive"

class Consistency(str, Enum):
    STRONG = "strong"
    EVENTUAL = "eventual"

# Dataclasses
@dataclass
class RegionConfig:
    name: str; url: str; weight: float; max_latency_ms: float
    priority: int; active: bool; region: str

@dataclass
class EdgeConfig:
    node_id: str; location: str; url: str; latency_ms: float
    capacity: int; specialized_models: list[str]

@dataclass
class SyncConfig:
    strategy: ReplicationStrategy; interval_seconds: int
    consistency: Consistency; timeout_seconds: int

@dataclass
class HybridConfig:
    cloud_provider: str; on_prem_url: str
    cost_threshold_per_1k: float
    model_tiers: dict[str, str]; sync_config: SyncConfig

# Classes
class GeoRouter:
    def __init__(self, regions: list[RegionConfig], *, strategy: RoutingStrategy, failover: bool = True) -> None: ...
    def route(self) -> RegionConfig: ...
    def mark_unhealthy(self, region: str) -> None: ...
    def mark_healthy(self, region: str) -> None: ...
    def update_latency(self, region: str, latency_ms: float) -> None: ...

@dataclass
class EdgeNode:
    config: EdgeConfig; status: str; last_health_check: float

class EdgeDeployment:
    def __init__(self, config: EdgeConfig) -> None: ...
    async def deploy(self, node_config: EdgeConfig) -> EdgeNode: ...
    def get_nearest(self, *, location: str) -> EdgeNode | None: ...
    def list_nodes(self) -> list[EdgeNode]: ...
    async def decommission(self, node_id: str) -> bool: ...
    def get_stats(self) -> dict[str, Any]: ...

class HybridCloudManager:
    def __init__(self, config: HybridConfig) -> None: ...
    def should_use_cloud(self, *, prompt_tokens: int, model: str) -> bool: ...
    def update_on_prem_metrics(self, **kwargs: Any) -> None: ...
    def get_llm_endpoint(self, model: str) -> str: ...
    def get_vector_store(self) -> str: ...

class DeploymentOrchestrator:
    def __init__(
        self,
        regions: list[RegionConfig],
        edge_config: EdgeConfig | None = None,
        hybrid_config: HybridConfig | None = None,
        *,
        routing_strategy: RoutingStrategy = RoutingStrategy.GEO_LATENCY,
    ) -> None: ...
    async def health_check(self) -> dict[str, Any]: ...
```

---

### `ai_core.recovery` — Disaster Recovery

**Partial coverage in UI** (only FailoverChain + BackupManager mentioned; full API missing):

```python
@dataclass
class HAConfig:
    primary: str; replicas: list[str]; heartbeat_interval_seconds: int
    failover_timeout_seconds: int; health_check_path: str; min_healthy_replicas: int

@dataclass
class RestorePoint:
    id: str; created_at: str; description: str
    vector_store_snapshot: dict[str, Any]
    index_metadata: dict[str, Any]; config_snapshot: dict[str, Any]

@dataclass
class BackupRecord:
    id: str; created_at: str; size_bytes: int
    destination: str; backend: str; status: str; verified: bool

class FailoverChain:
    def __init__(
        self,
        providers: list[str],
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
    ) -> None: ...
    def get_active_provider(self) -> str: ...
    def record_success(self, provider: str) -> None: ...
    def record_failure(self, provider: str) -> None: ...
    def status(self) -> dict[str, Any]: ...

class BaseBackupBackend(ABC):
    async def store(self, data: bytes, path: str) -> str: ...
    async def retrieve(self, path: str) -> bytes: ...
    async def list(self, prefix: str = "") -> list[str]: ...

class S3BackupBackend(BaseBackupBackend):
    def __init__(self, bucket: str, *, region: str = "us-east-1", prefix: str = "backups") -> None: ...

class LocalBackupBackend(BaseBackupBackend):
    def __init__(self, base_path: str) -> None: ...

class BackupManager:
    def __init__(
        self,
        *,
        backend: str = "local",
        encryption: bool = True,
        compression: bool = True,
        backend_config: dict[str, Any] | None = None,
    ) -> None: ...
    async def backup(self, data: dict[str, Any], *, description: str = "") -> BackupRecord: ...
    async def restore(self, backup_id: str) -> dict[str, Any]: ...
    async def list_backups(self, prefix: str = "") -> list[BackupRecord]: ...
    async def verify(self, backup_id: str) -> bool: ...
    @staticmethod
    def register_backend(name: str, cls: type[BaseBackupBackend]) -> None: ...

# Entirely absent from UI:
@dataclass
class DRTestResult:
    test_name: str; timestamp: str; success: bool
    metrics: dict[str, Any]; error: str

class DRTest:
    async def run_failover_test(
        self, failover_chain: FailoverChain, *, simulate_provider: str
    ) -> DRTestResult: ...
    async def run_backup_verify_test(self, backup_manager: BackupManager) -> DRTestResult: ...
    def get_results(self) -> list[DRTestResult]: ...

class ChaosEngineering:
    def simulate_failure(
        self, *, service: str, region: str = "", failure_type: str = "unavailable", duration_seconds: int = 60
    ) -> str: ...  # returns simulation ID
    def is_service_affected(self, service: str, region: str = "") -> bool: ...
    def stop_simulation(self, sim_id: str) -> None: ...
    def list_active(self) -> list[dict[str, Any]]: ...
```

---

## `ai_shared` — Entire Library (Wrong Import Paths Throughout)

> **All** examples in `SharedLibraryPage.tsx` use `from ai_core.X import Y`.  
> **Correct** path for every module below is `from ai_shared.X import Y`.

---

### `ai_shared.auth` — Authentication & RBAC

**UI says "8 permissions"; actual count is 9:**

```python
class Permission(str, Enum):
    READ = "read"; WRITE = "write"; EXECUTE = "execute"; ADMIN = "admin"
    DELETE = "delete"; MANAGE_USERS = "manage_users"; MANAGE_MODELS = "manage_models"
    VIEW_COSTS = "view_costs"; MANAGE_QUOTAS = "manage_quotas"   # ← 9th, missing from UI
```

**Missing `RBAC` methods**:

```python
class RBAC:
    def define_role(self, name: str, permissions: list[Permission], description: str = "") -> None: ...
    def has_permission(self, user: User, permission: Permission) -> bool: ...
    def get_permissions(self, user: User) -> set[Permission]: ...   # MISSING from UI
    def require(self, user: User, permission: Permission) -> None:  # MISSING — raises PermissionError
        ...
```

**Missing `APIKeyManager.revoke()` method**:

```python
class APIKeyManager:
    def register(self, key: str, *, roles: list[str], expires_at: str | None = None) -> None: ...
    def validate(self, key: str) -> AuthResult: ...
    def revoke(self, key: str) -> bool: ...   # MISSING from UI
```

**Missing `AuthResult` fields**:

```python
@dataclass
class AuthResult:
    success: bool
    user: User | None
    token: str
    expires_at: str
    error: str
```

---

### `ai_shared.cache` — Caching (ENTIRELY MISSING from UI)

```python
from ai_shared.cache import BaseCache, ExactCache, SemanticCache, RedisCache, MultiLayerCache

class BaseCache(ABC):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def clear(self) -> None: ...

class ExactCache(BaseCache):
    def __init__(self, *, max_size: int = 1000, default_ttl: int = 3600) -> None: ...

class SemanticCache(BaseCache):
    def __init__(
        self, embedder: BaseEmbedding, *,
        similarity_threshold: float = 0.92,
        max_size: int = 500,
        default_ttl: int = 3600,
    ) -> None: ...

class RedisCache(BaseCache):
    def __init__(self, *, url: str = "redis://localhost:6379", prefix: str = "ai_cache", default_ttl: int = 3600) -> None: ...

class MultiLayerCache(BaseCache):
    def __init__(self, layers: list[BaseCache]) -> None: ...
    # Implements L1→L2→… lookup with automatic backfill
```

---

### `ai_shared.cost` — Cost Management (PARTIALLY MISSING)

UI mentions cost tracking but doesn't document the actual API:

```python
from ai_shared.cost import CostTracker, CostOptimizer, QuotaManager, estimate_cost

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float: ...

@dataclass
class CostRecord:
    record_id: str; timestamp: str; provider: str; model: str
    input_tokens: int; output_tokens: int; cost_usd: float
    user_id: str; project: str; metadata: dict[str, Any]

class CostTracker:
    def record(
        self, provider: str, model: str, input_tokens: int, output_tokens: int,
        *, user_id: str = "", project: str = "", metadata: dict | None = None
    ) -> CostRecord: ...
    def total_cost(self, *, since: datetime | None = None) -> float: ...
    def cost_by_model(self, *, since: datetime | None = None) -> dict[str, float]: ...
    def cost_by_user(self, *, since: datetime | None = None) -> dict[str, float]: ...
    def cost_by_project(self, *, since: datetime | None = None) -> dict[str, float]: ...
    def summary(self, *, since: datetime | None = None) -> dict[str, Any]: ...

@dataclass
class OptimizationSuggestion:
    current_model: str; suggested_model: str
    estimated_savings_pct: float; reason: str

class CostOptimizer:
    def suggest(self, tracker: CostTracker) -> list[OptimizationSuggestion]: ...

@dataclass
class QuotaConfig:
    max_cost_usd: float = 100.0; max_requests: int = 10_000
    max_tokens: int = 10_000_000; period_hours: int = 24

@dataclass
class QuotaStatus:
    within_limits: bool; cost_used: float; cost_limit: float
    requests_used: int; requests_limit: int; tokens_used: int
    tokens_limit: int; exceeded: list[str]

class QuotaManager:
    def __init__(self, default_quota: QuotaConfig | None = None) -> None: ...
    def set_quota(self, key: str, quota: QuotaConfig) -> None: ...
    def check(self, key: str, tracker: CostTracker) -> QuotaStatus: ...
```

---

### `ai_shared.governance` — Data Governance (ENTIRELY MISSING)

```python
from ai_shared.governance import (
    DataClassifier, DataLineageTracker, PolicyEngine, AuditLogger, RetentionManager
)

class DataClassifier:
    def __init__(
        self, *, default_level: ClassificationLevel = ClassificationLevel.INTERNAL,
        rules: dict[str, ClassificationLevel] | None = None,
    ) -> None: ...
    def classify(self, text: str, *, metadata: dict | None = None) -> ClassificationResult: ...
    def add_rule(self, keyword: str, level: ClassificationLevel) -> None: ...

class DataLineageTracker:
    def add_source(self, name: str, *, metadata: dict | None = None) -> str: ...          # returns node_id
    def add_transform(self, name: str, source_id: str, *, transform_desc: str, metadata: dict | None = None) -> str: ...
    def add_output(self, name: str, source_id: str, *, metadata: dict | None = None) -> str: ...
    def get_lineage(self, node_id: str) -> dict[str, Any]: ...
    def to_dict(self) -> dict[str, Any]: ...

@dataclass
class Policy:
    name: str; condition: str; action: str  # "allow", "deny", "redact", "log"
    description: str; enabled: bool

class PolicyEngine:
    def add_policy(self, policy: Policy) -> None: ...
    def evaluate(self, context: dict[str, Any]) -> PolicyResult: ...

class AuditLogger:
    def __init__(self, *, max_entries: int = 100_000) -> None: ...
    def log(self, actor: str, action: str, resource: str, *, details: dict | None = None, outcome: str = "success") -> str: ...
    def query(self, *, actor: str | None, action: str | None, resource: str | None, limit: int = 100) -> list[AuditEntry]: ...
    def export(self) -> list[dict[str, Any]]: ...

@dataclass
class RetentionPolicy:
    name: str; data_type: str; retention_days: int
    action: str  # "delete", "archive", "anonymize"
    enabled: bool

class RetentionManager:
    def add_policy(self, policy: RetentionPolicy) -> None: ...
    def get_policies(self) -> list[RetentionPolicy]: ...
    async def enforce(self, current_time: datetime | None = None) -> list[dict[str, Any]]: ...
```

---

### `ai_shared.compliance` — Compliance (PARTIALLY MISSING)

UI references compliance frameworks but doesn't document the Python API:

```python
from ai_shared.compliance import ComplianceExporter, ComplianceMonitor, ComplianceFramework

class ComplianceFramework(str, Enum):
    SOC2 = "SOC2"; ISO27001 = "ISO27001"; GDPR = "GDPR"; CCPA = "CCPA"
    HIPAA = "HIPAA"; FEDRAMP = "FedRAMP"; PCI_DSS = "PCI_DSS"

class CertificationStatus(str, Enum):
    IMPLEMENTED = "implemented"; IN_PROGRESS = "in_progress"
    PLANNED = "planned"; NOT_PLANNED = "not_planned"

class ComplianceExporter:
    def register_certification(self, record: CertificationRecord) -> None: ...
    def register_dpa(self, dpa: DataProcessingAgreement) -> None: ...
    async def export(self, *, frameworks: list[str], period: str = "last_quarter", artifacts: list[str] | None = None) -> AuditPackage: ...
    async def generate_report(self, *, framework: str, controls: list[str] | None = None) -> dict[str, Any]: ...
    def get_certification_matrix(self) -> list[dict[str, str]]: ...

class ComplianceMonitor:
    def register_check(self, name: str, check_fn: Callable[..., ComplianceCheckResult]) -> None: ...
    async def run_all(self) -> list[ComplianceCheckResult]: ...
    async def verify_encryption(self, resource: str, *, encrypted: bool = True) -> ComplianceCheckResult: ...
    async def verify_backups(self, *, last_24h: bool = True, backup_count: int = 0) -> ComplianceCheckResult: ...
    async def verify_rbac_enforcement(self, *, roles_configured: int = 0) -> ComplianceCheckResult: ...
    async def verify_hipaa_phi_protection(self, *, pii_detector_enabled: bool = False) -> ComplianceCheckResult: ...
    async def verify_gdpr_consent(self, *, consent_records: int = 0) -> ComplianceCheckResult: ...
    async def verify_audit_logging(self, *, log_entries: int = 0) -> ComplianceCheckResult: ...
    async def verify_data_retention(self, *, policies_configured: int = 0) -> ComplianceCheckResult: ...
    def get_results(self, *, framework: str | None = None) -> list[ComplianceCheckResult]: ...
```

---

### `ai_shared.security` — Security (PARTIALLY MISSING)

UI shows "PII detection" and "content filtering" but not the actual API:

```python
from ai_shared.security import PIIDetector, ContentFilter, InputValidator

class PIIType(str, Enum):
    EMAIL = "email"; PHONE = "phone"; SSN = "ssn"; CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"; DATE_OF_BIRTH = "date_of_birth"; PASSPORT = "passport"; CUSTOM = "custom"

class PIIDetector:
    def __init__(
        self, *, enabled_types: set[PIIType] | None = None,
        custom_patterns: dict[str, re.Pattern] | None = None,
        redaction_char: str = "█",
    ) -> None: ...
    def detect(self, text: str) -> list[PIIMatch]: ...
    def redact(self, text: str) -> str: ...
    def has_pii(self, text: str) -> bool: ...

class ContentCategory(str, Enum):
    HARMFUL = "harmful"; HATEFUL = "hateful"; SEXUAL = "sexual"
    VIOLENCE = "violence"; SELF_HARM = "self_harm"; ILLEGAL = "illegal"
    PROMPT_INJECTION = "prompt_injection"

class ContentFilter:
    def __init__(
        self, *, blocked_categories: set[ContentCategory] | None = None,
        custom_blocklist: list[str] | None = None,
        check_injection: bool = True,
    ) -> None: ...
    def check(self, text: str) -> FilterResult: ...

class InputValidator:
    def __init__(
        self, *, max_length: int = 100_000, min_length: int = 1,
        strip_html: bool = True, strip_control_chars: bool = True,
    ) -> None: ...
    def validate(self, text: str) -> ValidationResult: ...
```

---

### `ai_shared.resilience` — Resilience (PARTIALLY MISSING)

UI mentions retry/circuit-breaker but not the actual Python API:

```python
from ai_shared.resilience import retry, CircuitBreaker, RateLimiter, with_timeout, RetryConfig

class BackoffStrategy(str, Enum):
    FIXED = "fixed"; EXPONENTIAL = "exponential"; LINEAR = "linear"

@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay: float = 1.0; max_delay: float = 60.0
    jitter: bool = True
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,)

def retry(config: RetryConfig | None = None) -> Callable:
    """Decorator — works on both sync and async functions."""

class CircuitState(str, Enum):
    CLOSED = "closed"; OPEN = "open"; HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self, *, failure_threshold: int = 5,
        recovery_timeout: float = 30.0, half_open_max_calls: int = 1,
    ) -> None: ...
    @property
    def state(self) -> CircuitState: ...
    async def call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any: ...
    def reset(self) -> None: ...

class RateLimiter:
    def __init__(self, *, max_calls: int = 60, period_seconds: float = 60.0) -> None: ...
    async def acquire(self) -> bool: ...
    async def wait(self) -> None: ...
    @property
    def remaining(self) -> int: ...
    def rate_limit(self) -> Callable: ...   # decorator

def with_timeout(seconds: float) -> Callable:
    """Decorator that enforces a timeout on async functions."""
```

---

### `ai_shared.memory` — Memory (PARTIALLY MISSING)

UI shows memory types in a list but no constructors or methods:

```python
from ai_shared.memory import (
    ConversationBufferMemory, ConversationSummaryMemory, VectorMemory,
    RedisMemory, PostgresMemory, EntityMemory, MemoryFactory
)

class BaseMemory(ABC):
    async def add(self, role: str, content: str, **kwargs: Any) -> None: ...
    async def get(self, **kwargs: Any) -> list[dict[str, str]]: ...
    async def clear(self) -> None: ...
    async def search(self, query: str, *, top_k: int = 5) -> list[dict[str, Any]]: ...

class ConversationBufferMemory(BaseMemory):
    def __init__(self, *, max_turns: int | None = None, return_messages: bool = True) -> None: ...

class ConversationSummaryMemory(BaseMemory):
    def __init__(self, llm: BaseLLM | None = None, *, max_summary_tokens: int = 500) -> None: ...

class VectorMemory(BaseMemory):
    def __init__(
        self, store: BaseVectorStore, embedder: BaseEmbedding,
        *, top_k: int = 5, relevance_threshold: float = 0.7,
    ) -> None: ...
    async def search(self, query: str, *, top_k: int | None = None) -> list[dict[str, Any]]: ...

class RedisMemory(BaseMemory):
    def __init__(self, *, url: str = "redis://localhost:6379", ttl_seconds: int = 3600, key_prefix: str = "ai_memory") -> None: ...

class PostgresMemory(BaseMemory):
    def __init__(self, connection_string: str, *, table_name: str = "ai_memory") -> None: ...

class EntityMemory(BaseMemory):
    def __init__(self, llm: BaseLLM | None = None) -> None: ...
    def get_entities(self) -> dict[str, dict[str, Any]]: ...   # extra method, missing from UI

class MemoryFactory:
    @staticmethod
    def create(memory_type: str, **kwargs: Any) -> BaseMemory: ...
    # memory_type values: "buffer", "summary", "vector", "redis", "postgres", "entity"
```

---

### `ai_shared.observability` — Observability (PARTIALLY MISSING)

UI mentions "LangSmith, Langfuse, OpenTelemetry" but not the actual API:

```python
from ai_shared.observability import Tracer, MetricsCollector, get_tracer, trace, metrics

class Span:
    span_id: str; trace_id: str; parent_id: str | None; name: str
    def set_attribute(self, key: str, value: Any) -> None: ...
    def add_event(self, name: str, attributes: dict | None = None) -> None: ...
    def end(self, *, status: str = "ok") -> None: ...
    @property
    def duration_ms(self) -> float: ...
    def to_dict(self) -> dict[str, Any]: ...

class Tracer:
    def add_exporter(self, exporter: SpanExporter) -> None: ...
    @contextmanager
    def trace(self, name: str) -> Iterator[Trace]: ...
    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]: ...
    @asynccontextmanager
    async def aspan(self, name: str, **attributes: Any) -> AsyncIterator[Span]: ...

class SpanExporter:
    def export(self, trace: Trace) -> None: ...

class ConsoleExporter(SpanExporter): ...
class LangSmithExporter(SpanExporter):
    def __init__(self, api_key: str, project: str = "default") -> None: ...
class LangfuseExporter(SpanExporter):
    def __init__(self, public_key: str, secret_key: str, host: str = "https://cloud.langfuse.com") -> None: ...
class OpenTelemetryExporter(SpanExporter):
    def __init__(self, endpoint: str, *, service_name: str = "ai-core") -> None: ...

def get_tracer() -> Tracer: ...  # returns global tracer instance
def trace(name: str | None = None, **attrs: Any) -> Callable: ...  # decorator

class MetricsCollector:
    def increment(self, name: str, value: float = 1.0, **labels: str) -> None: ...
    def observe(self, name: str, value: float, **labels: str) -> None: ...
    def set_gauge(self, name: str, value: float, **labels: str) -> None: ...
    def get_counter(self, name: str, **labels: str) -> float: ...
    def get_histogram(self, name: str, **labels: str) -> list[float]: ...
    def snapshot(self) -> dict[str, Any]: ...

metrics: MetricsCollector  # module-level singleton
```

---

### `ai_shared.tokens` — Token Budget (PARTIALLY MISSING)

UI mentions "token budget" but not the actual API — also note the `BudgetStrategy` enum here is **different** from the one in `schemas.py`:

```python
from ai_shared.tokens import TokenBudget, BudgetStrategy, count_tokens, estimate_cost

class BudgetStrategy(str, Enum):    # NOTE: DIFFERENT from schemas.BudgetStrategy
    GREEDY = "greedy"               # first-come-first-served
    PROPORTIONAL = "proportional"  # proportional to requested size
    PRIORITY = "priority"          # high-priority sections first
    FIXED = "fixed"                # each section gets its own cap

def count_tokens(text: str, model: str = "gpt-4") -> int: ...
def count_messages_tokens(messages: list[dict[str, str]], model: str = "gpt-4") -> int: ...
def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o") -> float: ...

class TokenBudget:
    def __init__(
        self, max_tokens: int, model: str = "gpt-4",
        *, strategy: BudgetStrategy = BudgetStrategy.PROPORTIONAL,
        reserve_output: int = 500,
    ) -> None: ...
    def add_section(
        self, name: str, content: str, *,
        priority: int = 1, min_tokens: int = 0, max_tokens: int | None = None,
    ) -> None: ...
    def fit(self) -> dict[str, str]: ...                  # returns truncated section texts
    def remaining_tokens(self) -> int: ...
    def usage_summary(self) -> dict[str, Any]: ...
```

---

### `ai_shared.plugins` — Plugin System (ENTIRELY MISSING)

```python
from ai_shared.plugins import PluginRegistry, plugin, PluginMetadata

class PluginProtocol(Protocol):
    name: str
    def initialize(self, config: dict[str, Any]) -> None: ...
    def shutdown(self) -> None: ...

@dataclass
class PluginMetadata:
    name: str; version: str = "0.1.0"; description: str = ""
    author: str = ""; category: str = "general"; dependencies: list[str] = []

class PluginRegistry:
    def register(self, plugin_class: type, *, metadata: PluginMetadata | None = None, config: dict | None = None) -> None: ...
    def register_from_module(self, module_path: str, *, config: dict | None = None) -> None: ...
    def unregister(self, name: str) -> bool: ...
    def get(self, name: str) -> Any: ...
    def list_plugins(self) -> list[PluginMetadata]: ...
    def has(self, name: str) -> bool: ...
    def add_hook(self, event: str, callback: Callable) -> None: ...
    def emit(self, event: str, *args: Any, **kwargs: Any) -> list[Any]: ...
    def shutdown_all(self) -> None: ...

def plugin(name: str, *, version: str = "0.1.0", category: str = "general", description: str = "") -> Callable[[type], type]:
    """Class decorator that attaches PluginMetadata to a class."""
```

---

### `ai_shared.logging_utils` — Structured Logging (PARTIALLY MISSING)

UI mentions "JSON logging" but not the actual API:

```python
from ai_shared.logging_utils import get_logger, LogContext, log_execution, JSONFormatter

class JSONFormatter(logging.Formatter):
    def __init__(self, *, include_extras: bool = True) -> None: ...
    def format(self, record: logging.LogRecord) -> str: ...

class LogContext:
    """Context manager that injects fields into all log records within its scope."""
    def __init__(self, **fields: Any) -> None: ...
    def __enter__(self) -> "LogContext": ...
    def __exit__(self, *exc: Any) -> None: ...

def get_logger(
    name: str, *, level: int = logging.INFO,
    json_output: bool = True, stream: Any = None,
) -> logging.Logger: ...

def log_execution(logger: logging.Logger | None = None, *, level: int = logging.INFO) -> Callable:
    """Decorator that logs function entry, exit, and duration (sync and async)."""
```

---

### `ai_shared.experiments` — Experiments & Feature Flags (ENTIRELY MISSING)

```python
from ai_shared.experiments import FeatureFlags, ExperimentManager, ExperimentAnalytics

@dataclass
class FeatureFlag:
    name: str; enabled: bool; rollout_pct: float; allowed_users: list[str]; metadata: dict

class FeatureFlags:
    def define(self, name: str, *, enabled: bool = False, rollout_pct: float = 100.0, allowed_users: list[str] | None = None) -> FeatureFlag: ...
    def is_enabled(self, name: str, *, user_id: str = "") -> bool: ...  # deterministic bucket hash
    def toggle(self, name: str, enabled: bool) -> None: ...
    def list_flags(self) -> list[FeatureFlag]: ...

@dataclass
class Experiment:
    experiment_id: str; name: str; description: str
    status: str  # "draft", "running", "paused", "completed"
    variants: list[ExperimentVariant]; created_at: str; started_at: str | None; ended_at: str | None

class ExperimentManager:
    def create(self, name: str, variants: list[dict[str, Any]], description: str = "") -> Experiment: ...
    def start(self, experiment_id: str) -> bool: ...
    def pause(self, experiment_id: str) -> bool: ...
    def complete(self, experiment_id: str) -> bool: ...
    def assign_variant(self, experiment_id: str, user_id: str) -> ExperimentVariant | None: ...
    def record_metric(self, experiment_id: str, variant_id: str, metric_name: str, value: float, *, metadata: dict | None = None) -> None: ...
    def get_experiment(self, experiment_id: str) -> Experiment | None: ...
    def list_experiments(self, *, status: str | None = None) -> list[Experiment]: ...

class ExperimentAnalytics:
    def __init__(self, manager: ExperimentManager) -> None: ...
    def summary(self, experiment_id: str) -> dict[str, Any]: ...
    def recommend_winner(self, experiment_id: str, metric_name: str) -> str | None: ...
```

---

### `ai_shared.models` — Model Registry & A/B Testing (PARTIALLY MISSING)

UI mentions "model lifecycle" but not the Python classes:

```python
from ai_shared.models import ModelRegistry, ABTestingFramework, RollbackManager

@dataclass
class ModelVersion:
    version_id: str; model_name: str; provider: str; config: dict
    status: str  # "active", "deprecated", "rollback"
    created_at: str; metrics: dict[str, float]; tags: list[str]

class ModelRegistry:
    def register(self, name: str, provider: str, *, config: dict | None = None, metrics: dict | None = None, tags: list[str] | None = None) -> ModelVersion: ...
    def get_active(self, name: str) -> ModelVersion | None: ...
    def promote(self, name: str, version_id: str) -> bool: ...
    def list_versions(self, name: str) -> list[ModelVersion]: ...
    def list_models(self) -> list[str]: ...
    def get_version(self, name: str, version_id: str) -> ModelVersion | None: ...
    def update_metrics(self, name: str, version_id: str, metrics: dict[str, float]) -> bool: ...

@dataclass
class ABTestConfig:
    test_id: str; name: str; model_a: str; model_b: str
    version_a: str; version_b: str; traffic_split: float
    status: str; created_at: str

class ABTestingFramework:
    def create_test(self, name: str, model_a: str, version_a: str, model_b: str, version_b: str, *, traffic_split: float = 0.5) -> ABTestConfig: ...
    def route_request(self, test_id: str) -> str: ...   # returns "a" or "b"
    def record_result(self, test_id: str, variant: str, *, latency_ms: float, quality_score: float, cost_usd: float, metadata: dict | None) -> None: ...
    def get_results(self, test_id: str) -> dict[str, Any]: ...
    def conclude(self, test_id: str, winner: str = "auto") -> str: ...

class RollbackManager:
    def __init__(self, registry: ModelRegistry) -> None: ...
    def rollback(self, model_name: str, target_version_id: str, *, reason: str = "") -> bool: ...
    def list_rollbacks(self, model_name: str | None = None) -> list[dict[str, Any]]: ...
```

---

## Summary Table

| Module | UI Coverage | Primary Gaps |
|--------|-------------|--------------|
| `ai_core.schemas` | Partial | `AgentState`, `PipelineHook`, `BudgetStrategy` enums; `ProvenanceMetadata`, `VectorDocument` full fields; `TokenUsage`, `Citation` models |
| `ai_core.config` | Wrong class name | `AICore` → `LibConfig`; missing all 20+ fields; `from_vault`, `from_aws_secrets`, `override`, `get` |
| `ai_core.rag` | Minimal | Full `ingest`/`query`/`stream`/`multi_query` signatures; all hook/setter methods |
| `ai_core.vectorstore` | Names only | Missing 5 constructors; `list_namespaces`, `collection_stats`; `VectorStoreFactory` |
| `ai_core.search` | Names only | `ParentChildSearch`, `ContextualCompressionSearch`, `StepBackSearch` constructors; `SearchStrategyFactory` |
| `ai_core.chunking` | Partial | `SlidingWindowChunker`, `ParagraphChunker`; `AgenticChunker.chunk_async`; `ChunkingEngine` static methods |
| `ai_core.prompts` | Partial | 3 missing `PromptStrategy` values; full `PromptEngine.build` params; `PromptRegistry`; `DynamicExampleSelector` |
| `ai_core.llm` | Partial | `generate_structured`; `LLMFactory` |
| `ai_core.embeddings` | Partial | `embed_documents`; `EmbeddingFactory.register` |
| `ai_core.reranker` | Partial | `RerankerFactory.register` |
| `ai_core.agents` | Partial | `AgentState`, `AgentMessage`, `MessageBus`, `ConflictResolution`, `Tool`, `ToolRegistry`, `tool()` decorator; `AgentRole`; `OrchestrationResult` 6 missing fields; `MultiAgentSystem` 3 missing params; **`AgentPipelineBuilder` must be removed — doesn't exist** |
| `ai_core.frameworks` | Wrong API | **`MCPServer` → `MCPAdapter`**; `build_retriever`, `build_workflow`, `build_crew`, `build_group_chat`, `for_framework` |
| `ai_core.eval` | Partial | `PipelineEvaluator`; `RAGEvaluator(llm=)` param; **`EvalReport.save/.export_html` must be removed** |
| `ai_core.deployment` | **None** | Entire module — `RoutingStrategy`, `ReplicationStrategy`, `Consistency` enums; all 4 dataclasses; `GeoRouter`, `EdgeDeployment`, `HybridCloudManager`, `DeploymentOrchestrator` |
| `ai_core.recovery` | Partial | `HAConfig`, `RestorePoint`, `BackupRecord` dataclasses; full `BackupManager` constructor; `DRTest`; `ChaosEngineering` |
| `ai_shared.auth` | Partial/Wrong path | Wrong import path; `MANAGE_QUOTAS` permission; `RBAC.get_permissions`, `RBAC.require`; `APIKeyManager.revoke` |
| `ai_shared.cache` | **None** | `ExactCache`, `SemanticCache`, `RedisCache`, `MultiLayerCache` — entire module absent |
| `ai_shared.cost` | Mention only | Full `CostTracker`, `CostOptimizer`, `QuotaManager` API |
| `ai_shared.governance` | **None** | `DataClassifier`, `DataLineageTracker`, `PolicyEngine`, `AuditLogger`, `RetentionManager` |
| `ai_shared.compliance` | Mention only | `ComplianceFramework` enum; full `ComplianceExporter` + `ComplianceMonitor` API |
| `ai_shared.security` | Mention only | `PIIType`, `ContentCategory` enums; full `PIIDetector`, `ContentFilter`, `InputValidator` API |
| `ai_shared.resilience` | Mention only | `BackoffStrategy`, `CircuitState` enums; `RetryConfig`; `retry()`, `with_timeout()` decorators; full `CircuitBreaker`, `RateLimiter` API |
| `ai_shared.memory` | Names only | Full constructors; `MemoryFactory`; `EntityMemory.get_entities` |
| `ai_shared.observability` | Mention only | `Span`, `Trace`, `Tracer`, all 4 exporters; `MetricsCollector`; `get_tracer()`, `trace()`, `metrics` |
| `ai_shared.tokens` | Mention only | `BudgetStrategy` enum; `count_tokens`, `estimate_cost` functions; full `TokenBudget` API |
| `ai_shared.plugins` | **None** | `PluginRegistry`, `plugin()` decorator — entire module absent |
| `ai_shared.logging_utils` | Mention only | `JSONFormatter`, `LogContext`, `get_logger`, `log_execution` |
| `ai_shared.experiments` | **None** | `FeatureFlags`, `ExperimentManager`, `ExperimentAnalytics` — entire module absent |
| `ai_shared.models` | Mention only | `ModelVersion`, `ModelRegistry`, `ABTestingFramework`, `RollbackManager` |
