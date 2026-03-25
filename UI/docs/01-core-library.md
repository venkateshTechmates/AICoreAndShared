# AI Core Library — Complete Module Reference

**Package:** `ai-core-lib`  
**Version:** 1.0.0  
**Python:** 3.11+  
**Type Safety:** Pydantic v2

---

## 1. RAG Engine (`ai_core.rag`)

The RAG (Retrieval-Augmented Generation) Engine is the primary orchestration layer for building production-grade knowledge-grounded AI systems.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Ingestion│→ │ Chunking │→ │Embedding │→ │  Upsert    │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Query   │→ │  Search  │→ │ Reranking│→ │ Generation │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Full API Reference

```python
from ai_core.rag import RAGPipeline, RAGConfig

config = RAGConfig(
    # Vector Store
    vector_db="pinecone",              # pinecone | weaviate | qdrant | chroma | milvus | pgvector | redis
    
    # Embedding
    embedding_model="text-embedding-3-large",
    embedding_dimensions=3072,
    embedding_batch_size=512,
    
    # LLM
    llm_provider="openai",             # openai | anthropic | azure | bedrock | vertex | ollama
    llm_model="gpt-4o",
    llm_temperature=0.1,
    llm_max_tokens=4096,
    
    # Chunking
    chunking_strategy="semantic",       # fixed | recursive | semantic | sentence | agentic | document_aware
    chunk_size=512,
    chunk_overlap=50,
    
    # Search
    search_strategy="hybrid",           # dense | sparse | hybrid | mmr | multi_query | hyde | self_query
    top_k=10,
    top_k_after_rerank=3,
    
    # Reranking
    reranker="cohere",                  # cohere | bge | cross_encoder | llm_reranker | none
    
    # Advanced
    prompt_strategy="few_shot",         # zero_shot | few_shot | chain_of_thought | react | rag
    citation_tracking=True,
    streaming=True,
    contextual_compression=True,
    max_context_tokens=8000,
)

rag = RAGPipeline(config)

# ── Ingestion ──
await rag.ingest(
    documents=docs,
    namespace="finance-q4",
    preprocessing=["clean_html", "remove_headers", "normalize_whitespace"],
    metadata_extractor="auto",
)

# ── Single Query ──
response = await rag.query(
    query="What were the Q4 revenue drivers?",
    namespace="finance-q4",
    filters={"department": "sales", "year": 2025},
    prompt_strategy="chain_of_thought",
    include_sources=True,
)

# Access response
print(response.answer)           # Generated answer
print(response.sources)          # List of source documents with scores
print(response.tokens_used)      # Token consumption { input, output, total }
print(response.latency_ms)       # End-to-end latency
print(response.citations)        # Mapped citations back to source chunks

# ── Streaming Query ──
async for chunk in rag.stream(query="Summarize the risk factors"):
    print(chunk.text, end="", flush=True)

# ── Multi-Index RAG ──
response = await rag.multi_query(
    query="Compare our Q3 and Q4 performance",
    namespaces=["finance-q3", "finance-q4"],
    merge_strategy="interleave",        # interleave | concatenate | rrf
)

# ── Batch Ingestion ──
results = await rag.batch_ingest(
    documents=large_doc_set,
    namespace="knowledge-base",
    batch_size=100,
    parallel_workers=4,
    on_progress=lambda p: print(f"{p.completed}/{p.total}"),
)
```

### Pipeline Hooks

```python
from ai_core.rag import RAGPipeline, PipelineHook

# Register lifecycle hooks
@rag.hook(PipelineHook.PRE_RETRIEVAL)
async def add_metadata_filter(query_context):
    query_context.filters["tenant_id"] = current_tenant.id
    return query_context

@rag.hook(PipelineHook.POST_RETRIEVAL)
async def log_retrieved_docs(documents):
    logger.info(f"Retrieved {len(documents)} documents")
    return documents

@rag.hook(PipelineHook.PRE_GENERATION)
async def compress_context(context):
    if context.token_count > 8000:
        return await context.compress(strategy="summary")
    return context

@rag.hook(PipelineHook.POST_GENERATION)
async def audit_response(response):
    await audit_logger.log(response)
    return response
```

---

## 2. Vector Database Abstraction (`ai_core.vectorstore`)

### Factory Pattern

```python
from ai_core.vectorstore import VectorStoreFactory, VectorDocument, SearchQuery

# Create store — swap backend with config only
store = VectorStoreFactory.create(
    provider="qdrant",                   # Any supported provider
    collection="knowledge_base",
    config={
        "url": "http://localhost:6333",
        "api_key": "${QDRANT_API_KEY}",
        "prefer_grpc": True,
    },
)

# ── Upsert Documents ──
await store.upsert(documents=[
    VectorDocument(
        id="doc_001",
        vector=[0.1, 0.2, ...],         # Pre-computed or auto-embedded
        text="Revenue increased 15% YoY driven by cloud services.",
        metadata={"department": "finance", "year": 2025, "quarter": "Q4"},
        namespace="finance",
        source_uri="s3://reports/q4_2025.pdf",
        chunk_index=42,
    )
])

# ── Search ──
results = await store.search(
    query=SearchQuery(
        vector=embedding,                # Or text= for auto-embedding
        top_k=10,
        filters={"department": "finance"},
        strategy="hybrid",
        score_threshold=0.7,
        include_metadata=True,
    )
)

for result in results:
    print(f"Score: {result.score} | Text: {result.text[:100]}")

# ── Namespace Management ──
await store.delete(ids=["doc_001", "doc_002"])
await store.delete_namespace("old_tenant")
namespaces = await store.list_namespaces()
stats = await store.collection_stats()
```

### Supported Providers

| Provider | Type | Key Features | Best For |
|---|---|---|---|
| **Pinecone** | Managed Cloud | Serverless, pod-based, hybrid search | Production SaaS |
| **Qdrant** | Open Source / Cloud | Rust core, gRPC, filtering | Performance-critical |
| **Weaviate** | Open Source / Cloud | GraphQL, modules, multi-modal | Complex queries |
| **Chroma** | Open Source | In-process, simple API | Local dev / prototyping |
| **Milvus / Zilliz** | Open Source / Cloud | GPU acceleration, massive scale | Large-scale deployments |
| **PgVector** | Postgres Extension | SQL-integrated, ACID | Existing Postgres infra |
| **Redis VSS** | In-Memory | Sub-millisecond, ephemeral | Real-time / caching |
| **OpenSearch** | AWS Managed | kNN plugin, hybrid | AWS-centric orgs |
| **Azure AI Search** | Azure Managed | Cognitive skills, hybrid | Azure ecosystem |

---

## 3. Vector Search Strategies (`ai_core.search`)

### Strategy Reference

```python
from ai_core.search import SearchStrategyFactory

# ── Hybrid Search (Dense + Sparse with RRF) ──
strategy = SearchStrategyFactory.create(
    strategy="hybrid",
    dense_weight=0.7,
    sparse_weight=0.3,
    fusion="rrf",                       # rrf | weighted | dbsf
)
results = await strategy.search(query, store)

# ── MMR (Max Marginal Relevance) — Diversity-aware ──
strategy = SearchStrategyFactory.create(
    strategy="mmr",
    lambda_mult=0.7,                    # 0 = max diversity, 1 = max relevance
    fetch_k=20,                         # Fetch 20, return top_k diverse
)

# ── Multi-Query — LLM generates N variants ──
strategy = SearchStrategyFactory.create(
    strategy="multi_query",
    num_queries=3,
    llm="gpt-4o-mini",
    merge="rrf",
)

# ── HyDE — Hypothetical Document Embedding ──
strategy = SearchStrategyFactory.create(
    strategy="hyde",
    llm="gpt-4o",
    num_hypothetical=1,
)

# ── Self-Query — LLM generates structured filter ──
strategy = SearchStrategyFactory.create(
    strategy="self_query",
    llm="gpt-4o",
    metadata_schema={"department": "str", "year": "int", "category": "str"},
)

# ── Parent-Child — Return parent context ──
strategy = SearchStrategyFactory.create(
    strategy="parent_child",
    child_chunk_size=200,
    parent_chunk_size=1000,
)
```

### Strategy Comparison Matrix

| Strategy | Latency | Relevance | Diversity | Token Cost | Best For |
|---|---|---|---|---|---|
| Dense (ANN) | Low | High | Low | None | Semantic similarity |
| Sparse (BM25) | Low | Medium | Low | None | Keyword/exact match |
| Hybrid (RRF) | Medium | Very High | Medium | None | General production |
| MMR | Medium | High | Very High | None | Diverse results |
| Multi-Query | High | Very High | High | Medium | Ambiguous queries |
| HyDE | High | High | Medium | Medium | Low-recall domains |
| Self-Query | Medium | High | Medium | Low | Filtered search |
| Step-Back | High | Very High | Medium | Medium | Reasoning-heavy |
| Parent-Child | Medium | High | Medium | None | Hierarchical docs |
| Contextual Compression | Medium | High | Low | Medium | Token budget |

---

## 4. Chunking Engine (`ai_core.chunking`)

### All Strategies

```python
from ai_core.chunking import ChunkingEngine, ChunkingConfig

# ── Semantic Chunking ──
engine = ChunkingEngine(
    strategy="semantic",
    config=ChunkingConfig(
        embedding_model="text-embedding-3-small",
        breakpoint_threshold=0.75,
        min_chunk_size=100,
        max_chunk_size=1000,
    )
)
chunks = engine.chunk(documents)

# ── Recursive Character ──
engine = ChunkingEngine(
    strategy="recursive",
    config=ChunkingConfig(
        separators=["\n\n", "\n", ". ", " "],
        chunk_size=512,
        chunk_overlap=50,
    )
)

# ── Document-Aware ──
engine = ChunkingEngine(
    strategy="document_aware",
    config=ChunkingConfig(
        respect_headings=True,
        min_chunk_size=200,
        max_chunk_size=1500,
        preserve_tables=True,
    )
)

# ── Agentic / LLM-Based ──
engine = ChunkingEngine(
    strategy="agentic",
    config=ChunkingConfig(
        llm_model="gpt-4o-mini",
        instructions="Split at logical topic boundaries. Keep related concepts together.",
    )
)

# ── Code-Aware ──
engine = ChunkingEngine(
    strategy="code",
    config=ChunkingConfig(
        language="python",
        include_comments=True,
        split_by="function",            # function | class | module
    )
)

# ── Markdown/HTML ──
engine = ChunkingEngine(
    strategy="markdown",
    config=ChunkingConfig(
        split_headings=True,
        tag_weights={"h1": 3, "h2": 2, "h3": 1},
        preserve_code_blocks=True,
    )
)
```

### Chunking Strategy Decision Matrix

| Strategy | Structure Awareness | Speed | Quality | Use Case |
|---|---|---|---|---|
| Fixed-Size | None | Fastest | Low | Quick prototyping |
| Recursive Character | Separator-based | Fast | Medium | General text |
| Sentence | Sentence boundaries | Fast | Medium | NLP pipelines |
| Semantic | Embedding-based | Slow | Very High | Production RAG |
| Document-Aware | Heading/section | Medium | High | Structured docs |
| Agentic (LLM) | Full understanding | Slowest | Highest | Critical content |
| Code-Aware | AST-based | Fast | High | Source code |
| Markdown/HTML | Tag-based | Fast | High | Web content |

---

## 5. Prompt Engineering Module (`ai_core.prompts`)

### Template Registry

```python
from ai_core.prompts import PromptRegistry, PromptTemplate, PromptStrategy

# ── Register versioned template ──
PromptRegistry.register(
    PromptTemplate(
        name="legal_summary",
        version="1.2",
        strategy=PromptStrategy.FEW_SHOT,
        system="You are a senior legal analyst. Analyze documents with precision.",
        examples=[
            {"input": "Contract clause about liability...", "output": "Summary: ..."},
            {"input": "Indemnification terms state...", "output": "Summary: ..."},
        ],
        user_template="Summarize the following document:\n\n{document}",
        metadata={"domain": "legal", "author": "ai-team"},
    )
)

# ── Render prompt ──
prompt = PromptRegistry.render("legal_summary", document=doc_text)

# ── List all templates ──
templates = PromptRegistry.list(domain="legal")

# ── Version management ──
history = PromptRegistry.get_versions("legal_summary")
PromptRegistry.rollback("legal_summary", version="1.0")
```

### All Supported Strategies

| Strategy | Description | Python Enum | Best For |
|---|---|---|---|
| Zero-Shot | Instruction only, no examples | `PromptStrategy.ZERO_SHOT` | Simple tasks |
| One-Shot | Single example | `PromptStrategy.ONE_SHOT` | Format clarification |
| Few-Shot | Multiple curated examples | `PromptStrategy.FEW_SHOT` | Complex domain tasks |
| Chain-of-Thought | Step-by-step reasoning | `PromptStrategy.CHAIN_OF_THOUGHT` | Math/logic |
| Zero-Shot CoT | CoT without examples | `PromptStrategy.ZERO_SHOT_COT` | Reasoning |
| Self-Consistency | N paths + majority vote | `PromptStrategy.SELF_CONSISTENCY` | Reliability |
| Tree-of-Thought | Multi-branch exploration | `PromptStrategy.TREE_OF_THOUGHT` | Planning |
| ReAct | Reason + Act with tools | `PromptStrategy.REACT` | Agent tasks |
| Reflexion | Self-critique loop | `PromptStrategy.REFLEXION` | Quality improvement |
| Program-of-Thought | Code generation + exec | `PromptStrategy.PROGRAM_OF_THOUGHT` | Quantitative |
| Role Prompting | Expert persona | `PromptStrategy.ROLE` | Domain expertise |
| Meta Prompting | LLM designs own prompt | `PromptStrategy.META` | Prompt discovery |
| Skeleton-of-Thought | Parallel sub-answers | `PromptStrategy.SKELETON` | Latency reduction |
| RAG Prompting | Context injection | `PromptStrategy.RAG` | Knowledge-grounded |
| Directional Stimulus | Guided hint | `PromptStrategy.DIRECTIONAL` | Guided generation |

### Dynamic Example Selection

```python
from ai_core.prompts import DynamicExampleSelector

selector = DynamicExampleSelector(
    examples=example_pool,
    strategy="semantic",                # semantic | random | mmr | bm25 | maximal_marginal
    k=3,
    embedding_model="text-embedding-3-small",
)

# Auto-select most relevant examples for the query
few_shot_prompt = selector.select_and_render(query=user_input)
```

---

## 6. Agentic AI Framework (`ai_core.agents`)

### Overview

The v1.1.0 agents module provides a complete enterprise multi-agent orchestration system built on six coordination modes, a pub/sub `MessageBus`, fluent `AgentPipelineBuilder`, and a rich `OrchestrationResult` schema.

### Agent Types & Tool Registry

```python
from ai_core.agents import Tool, ToolRegistry, AgentExecutor, AgentType

# ── Register tools ──
@ToolRegistry.register
class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for current information"
    
    async def run(self, query: str) -> str:
        ...

@ToolRegistry.register
class SQLQueryTool(Tool):
    name = "sql_query"
    description = "Execute SQL queries against the data warehouse"
    input_schema = {"query": "str", "database": "str"}
    
    async def run(self, query: str, database: str = "analytics") -> str:
        ...

# ── Create agent via factory ──
agent = AgentExecutor.create(
    AgentType.REACT,                     # react | plan_execute | reflexion | function_call | structured
    llm=llm,
    tools=[ToolRegistry.get("web_search"), ToolRegistry.get("sql_query")],
    max_iterations=10,
    verbose=True,
)

result = await agent.run("Research and summarize AI trends in 2026")
print(result.output)
print(result.steps)         # Reasoning trace
print(result.tool_calls)    # Tool invocations
print(result.tokens_used)   # Total token consumption
```

### FunctionCallAgent — Structured Tool Schema

Uses OpenAI-style function-calling API (structured `tool_calls`) with a text-parsing fallback for models that don't emit `tool_calls` natively:

```python
from ai_core.schemas import AgentType

fc_agent = AgentExecutor.create(
    AgentType.FUNCTION_CALL,
    llm=llm,
    tools=[ToolRegistry.get("web_search"), ToolRegistry.get("sql_query")],
)
result = await fc_agent.run("How many orders shipped last week?")
# result.tool_calls — list of {"tool": ..., "args": {...}, "result": "..."}
for tc in result.tool_calls:
    print(f"Called {tc['tool']}({tc['args']}) → {tc['result']}")
```

### StructuredOutputAgent — Pydantic Validation

Prompts the LLM to return JSON, then validates the response against an optional Pydantic model:

```python
from pydantic import BaseModel
from ai_core.schemas import AgentType

class RiskAssessment(BaseModel):
    risk_level: str          # low | medium | high | critical
    confidence: float        # 0.0–1.0
    factors: list[str]
    recommendation: str

s_agent = AgentExecutor.create(AgentType.STRUCTURED, llm=llm)
result = await s_agent.run(
    "Assess the credit risk for applicant ID A-2024-001.",
    output_schema=RiskAssessment,
)
print(result.output)   # validated JSON string from RiskAssessment.model_dump_json()
```

### BaseAgent — Built-in Retry

All agents inherit `_call_llm_with_retry()` for resilient LLM calls with exponential backoff:

```python
# Used internally; also available in custom agents
response = await self._call_llm_with_retry(
    prompt_or_messages,
    max_retries=3,       # default 3
    initial_delay=1.0,   # seconds; doubles each retry (1 s → 2 s → 4 s)
)
```

### Six Coordination Modes


```python
from ai_core.agents import MultiAgentSystem
from ai_core.schemas import CoordinationMode

# ── 1. Sequential — one agent at a time, output chains forward ──
system = MultiAgentSystem(
    agents=[research_agent, analysis_agent, writer_agent],
    mode=CoordinationMode.SEQUENTIAL,
)
result = await system.run("Summarise the Q4 earnings report.")

# ── 2. Parallel — all agents run concurrently, results fan in ──
system = MultiAgentSystem(
    agents=[pricing_agent, inventory_agent, fraud_agent, review_agent],
    mode=CoordinationMode.PARALLEL,
)
result = await system.run("Evaluate order #ORD-2024-8821")

# ── 3. Debate — structured critique over N rounds until consensus ──
system = MultiAgentSystem(
    agents=[bull_agent, bear_agent, moderator_agent],
    mode=CoordinationMode.DEBATE,
    rounds=3,
)
result = await system.run("Estimate fair value for property at 12 Oak Lane")
print(result.consensus)

# ── 4. Hierarchical — supervisor routes to specialist workers ──
system = MultiAgentSystem(
    agents=[supervisor_agent, triage_agent, specialist_agent],
    mode=CoordinationMode.HIERARCHICAL,
)
result = await system.run("Process patient intake for cardiology")

# ── 5. Swarm — agents share a collaborative workspace ──
system = MultiAgentSystem(
    agents=[extractor_agent, validator_agent, mapper_agent],
    mode=CoordinationMode.SWARM,
)
result = await system.run("Build knowledge graph from the contract document")

# ── 6. Supervisor — coordinator owns final decision authority ──
system = MultiAgentSystem(
    agents=[coordinator_agent, underwriter_agent, compliance_agent],
    mode=CoordinationMode.SUPERVISOR,
)
result = await system.run("Process loan application #L-2024-5521")
print(result.results['decision'])   # APPROVE | DENY | REFER
```

### Coordination Mode Reference

| Mode | Pattern | Ideal For |
|---|---|---|
| `SEQUENTIAL` | A → B → C | Report generation, pipelines with data dependencies |
| `PARALLEL` | A + B + C → merge | Intelligence gathering, risk scoring |
| `DEBATE` | A ↔ B (N rounds) | Valuation, investment analysis, adversarial review |
| `HIERARCHICAL` | Supervisor → workers | Medical triage, compliance workflows |
| `SWARM` | Shared workspace | Knowledge graph construction, entity extraction |
| `SUPERVISOR` | Coordinator → dynamic dispatch | Loan underwriting, multi-step approvals |

### MessageBus

All agents within a `MultiAgentSystem` share a `MessageBus` that provides topic-based pub/sub routing, dead-letter queues, and message history.

```python
from ai_core.agents import MessageBus, AgentMessage

bus = MessageBus()

# Publish a message to a topic
await bus.publish(
    topic="analysis.ready",
    message=AgentMessage(
        sender="AnalysisAgent",
        content="Analysis complete: revenue up 12% YoY",
        metadata={"confidence": 0.95},
    ),
)

# Subscribe to a topic
bus.subscribe("analysis.ready", callback=my_handler)

# Inspect dead letters
print(bus.dead_letters)

# Full message history
for msg in bus.history:
    print(f"{msg.sender} → {msg.topic}: {msg.content[:50]}")
```

### AgentPipelineBuilder

A fluent builder for composing multi-stage agent pipelines:

```python
from ai_core.agents import AgentPipelineBuilder
from ai_core.schemas import CoordinationMode

pipeline = (
    AgentPipelineBuilder()
    .add_stage("intake",    intake_agent)
    .add_stage("analyse",   analysis_agent)
    .add_stage("report",    writer_agent)
    .with_mode(CoordinationMode.SEQUENTIAL)
    .build()
)

result = await pipeline.run(
    "Produce a compliance report for Q1 2025",
    context={"department": "finance", "framework": "SOC2"},
)

print(result.final_answer)
print(result.metadata['stages_completed'])
print(result.cost)
```

### OrchestrationResult Schema

```python
@dataclass
class OrchestrationResult:
    task: str
    mode: CoordinationMode
    results: dict[str, Any]     # per-agent outputs keyed by agent name
    consensus: str | None       # populated by DEBATE mode
    final_answer: str
    metadata: dict[str, Any]    # rounds_completed, stages, workspace state, etc.
    cost: float                 # total $ across all agent calls
    duration_ms: float
```

---

## 7. Multi-Framework Orchestration (`ai_core.frameworks`)

### Unified Adapter Layer

```python
from ai_core.frameworks import FrameworkAdapter

# ── LangChain ──
lc_adapter = FrameworkAdapter.for_framework("langchain")
chain = lc_adapter.build_rag_chain(config=rag_config)
result = await chain.ainvoke({"question": "What is the refund policy?"})

# ── LangGraph ──
lg_adapter = FrameworkAdapter.for_framework("langgraph")
graph = lg_adapter.build_workflow(spec=workflow_spec)
result = await graph.ainvoke({"query": "Analyze this contract"})

# ── CrewAI ──
crew_adapter = FrameworkAdapter.for_framework("crewai")
crew = crew_adapter.build_crew(spec=crew_spec)
result = await crew.kickoff(inputs={"topic": "AI regulation"})

# ── AutoGen ──
ag_adapter = FrameworkAdapter.for_framework("autogen")
chat = ag_adapter.build_group_chat(spec=chat_spec)
result = await chat.run("Build a market analysis")

# ── MCP (Model Context Protocol) ──
from ai_core.frameworks.mcp import MCPServer

server = MCPServer(name="enterprise-rag-server")

@server.tool()
async def search_knowledge_base(query: str, namespace: str) -> list[str]:
    """Search the enterprise knowledge base."""
    return await rag.query(query, namespace=namespace)

@server.resource(uri_template="docs://{doc_id}")
async def get_document(doc_id: str) -> MCPResource:
    return await document_store.get(doc_id)

server.run(transport="stdio")
```

### Framework Support Matrix

| Capability | LangChain | LangGraph | CrewAI | AutoGen | MCP | Vertex AI | Bedrock |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| RAG Pipeline | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tool / Function Calling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-Agent | ✅ | ✅ | ✅ | ✅ | ◐ | ✅ | ◐ |
| Stateful Workflow | ❌ | ✅ | ◐ | ◐ | ❌ | ◐ | ❌ |
| Streaming | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Memory | ✅ | ✅ | ✅ | ✅ | ◐ | ◐ | ◐ |
| Human-in-the-Loop | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 8. Evaluation Suite (`ai_core.eval`)

### RAG Evaluation

```python
from ai_core.eval import RAGEvaluator, RAGASEvaluator, DeepEvalEvaluator, PipelineEvaluator

# ── Standard RAG Evaluator ──
evaluator = RAGEvaluator(
    metrics=[
        "faithfulness",          # Is the answer grounded in context?
        "answer_relevancy",      # Is the answer relevant to the question?
        "context_recall",        # Were relevant docs retrieved?
        "context_precision",     # Are retrieved docs relevant?
    ],
    llm_judge="gpt-4o",
    batch_size=50,
)

# Run evaluation
report = await evaluator.evaluate(
    questions=test_set,
    pipeline=rag,
    ground_truth=golden_answers,
)

# Access metrics — .summary() returns dict[str, float]
scores = report.summary()
# {
#   "faithfulness": 0.92,
#   "answer_relevancy": 0.89,
#   "context_recall": 0.87,
#   "context_precision": 0.91,
# }

# ── RAGAS integration ──
ragas_evaluator = RAGASEvaluator(
    metrics=["faithfulness", "answer_relevancy", "context_recall"],
    llm="gpt-4o",
)
report = await ragas_evaluator.evaluate(dataset=eval_dataset)

# ── DeepEval integration ──
deepeval_evaluator = DeepEvalEvaluator(
    metrics=["GEval", "Faithfulness", "HallucinationMetric"],
    model="gpt-4o",
)
report = await deepeval_evaluator.evaluate(test_cases=test_cases)

# ── Pipeline Evaluator (end-to-end) ──
pipeline_evaluator = PipelineEvaluator(
    pipeline=rag_pipeline,
    metrics=["faithfulness", "latency_p50", "latency_p99", "cost"],
)
report = await pipeline_evaluator.run(test_set)
print(report.summary())  # dict[str, float]
```

### Supported Evaluation Frameworks

| Framework | Class | Focus | Integration Level |
|---|---|---|---|
| RAGAS | `RAGASEvaluator` | RAG-specific metrics | Full |
| DeepEval | `DeepEvalEvaluator` | Comprehensive LLM eval | Full |
| Custom | `RAGEvaluator` | User-defined metrics | Built-in |
| Pipeline | `PipelineEvaluator` | End-to-end quality | Built-in |

---

## 9. Deployment & Geo-Routing (`ai_core.deployment`)

Enterprise-grade geo-routing, edge deployment, and hybrid cloud orchestration.

### Geo-Routing

```python
from ai_core.deployment import GeoRouter, RoutingStrategy, EdgeDeployment

# ── Geo-aware router ──
router = GeoRouter(
    strategy=RoutingStrategy.LATENCY,   # LATENCY | COST | COMPLIANCE | ROUND_ROBIN
    regions=[
        {"name": "us-east-1", "provider": "openai", "model": "gpt-4o"},
        {"name": "eu-west-1", "provider": "azure", "model": "gpt-4-turbo"},
        {"name": "ap-southeast-1", "provider": "anthropic", "model": "claude-3-sonnet"},
    ],
)

# Route by client location
endpoint = await router.route(request, client_region="eu-west-1")
response = await endpoint.llm.generate(request.prompt)
```

### Edge Deployment

```python
from ai_core.deployment import EdgeDeployment, ReplicationStrategy

# Deploy models to edge nodes
edge = EdgeDeployment(
    node_id="edge-node-1",
    region="us-west-2",
    replication=ReplicationStrategy.ACTIVE_ACTIVE,
    models=["llama-3-8b", "nomic-embed-text"],
    max_concurrent=100,
)

await edge.deploy()
response = await edge.infer(prompt="Analyze this document...")
health = await edge.health_check()
# {"status": "healthy", "latency_p99_ms": 45, "models": ["llama-3-8b", ...]}
```

### Hybrid Cloud Manager

```python
from ai_core.deployment import HybridCloudManager, Consistency

# Manage workload distribution across cloud providers
manager = HybridCloudManager(
    primary="azure",
    fallback="aws",
    consistency=Consistency.EVENTUAL,
    cost_threshold_usd_per_day=500.0,
)

# Auto-routes: compliance data → on-prem, burst → cloud
result = await manager.execute(task, data_classification="confidential")

# Get cost breakdown
report = manager.cost_report()
# {"azure": 240.50, "aws": 85.20, "on_prem": 12.30, "total": 338.00}
```

### Deployment Orchestrator

```python
from ai_core.deployment import DeploymentOrchestrator

# Full orchestration of multi-region pipeline deployment
orchestrator = DeploymentOrchestrator(
    geo_router=router,
    edge_nodes=[edge_us, edge_eu, edge_ap],
    cloud_manager=manager,
)

# Deploy a new pipeline version with zero downtime
await orchestrator.rolling_deploy(
    pipeline=my_pipeline,
    strategy="blue_green",
    health_check_interval=30,
    rollback_on_failure=True,
)
```

---

## 10. Recovery & Disaster Recovery (`ai_core.recovery`)

Enterprise-grade failover, backup, DR testing, and chaos engineering.

### Failover Chain

```python
from ai_core.recovery import FailoverChain

# Chain of fallback LLM providers
chain = FailoverChain(
    steps=[
        {"provider": "openai",    "model": "gpt-4o"},
        {"provider": "anthropic", "model": "claude-3-sonnet"},
        {"provider": "azure",     "model": "gpt-4-turbo"},
        {"provider": "ollama",    "model": "llama3"},          # last resort: local
    ],
    timeout_per_step=10.0,
    on_failure="next",    # next | raise | return_empty
)

response = await chain.execute(prompt="Summarize this document...")
print(response.used_step)   # Which provider/model actually responded
```

### Backup Manager

```python
from ai_core.recovery import BackupManager

backup = BackupManager(
    storage_backend="s3",
    bucket="my-ai-backups",
    encryption=True,
    retention_days=90,
    schedule="0 2 * * *",     # 2am daily via cron
)

# Backup vector store
await backup.backup_vectorstore(store=qdrant_store, namespace="enterprise_kb")

# Backup conversation memory
await backup.backup_memory(memory=redis_memory, user_ids=active_users)

# Restore from backup
await backup.restore(
    backup_id="backup-2024-01-15-020000",
    target=qdrant_store,
    dry_run=True,
)
```

### Disaster Recovery Testing

```python
from ai_core.recovery import DRTest

dr = DRTest(
    pipeline=production_pipeline,
    backup_manager=backup,
    failover_chain=chain,
)

# Run DR drill
results = await dr.run_drill(
    scenarios=["provider_outage", "network_partition", "data_corruption"],
    target_rto_seconds=30,    # Recovery Time Objective
    target_rpo_seconds=300,   # Recovery Point Objective
)

for scenario in results:
    print(f"{scenario.name}: RTO={scenario.actual_rto}s RPO={scenario.actual_rpo}s PASSED={scenario.passed}")
```

### Chaos Engineering

```python
from ai_core.recovery import ChaosEngineering

chaos = ChaosEngineering(
    pipeline=my_pipeline,
    safe_mode=True,              # Prevent production impact
)

# Inject failures to test resilience
await chaos.inject_latency(target="llm", delay_ms=2000, probability=0.3)
await chaos.inject_error(target="vectorstore", error_type="timeout", probability=0.1)
await chaos.inject_outage(target="openai", duration_seconds=60)

# Run a full chaos experiment
report = await chaos.run_experiment(
    name="LLM Provider Resilience",
    duration_seconds=300,
    failure_rate=0.2,
)
print(report.summary())
# {"availability": 0.994, "p99_latency_ms": 3200, "failover_success_rate": 1.0}
```
