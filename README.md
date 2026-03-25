# AI Enterprise Toolkit

**Version:** 1.1.0 | **Python:** 3.11+ | **License:** MIT

[![GitHub Pages](https://img.shields.io/badge/docs-live-blue?logo=github)](https://venkateshTechmates.github.io/AICoreAndShared/)
[![GitHub Repo](https://img.shields.io/badge/repo-AICoreAndShared-181717?logo=github)](https://github.com/venkateshTechmates/AICoreAndShared)
[![Tests](https://img.shields.io/badge/tests-247%20passing-brightgreen)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-90%25+-green)](#testing)

> **Live Documentation:** https://venkateshTechmates.github.io/AICoreAndShared/

A production-ready, enterprise-grade AI library split into two packages:

| Package | Purpose |
|---|---|
| `ai_core` | RAG pipelines, LLMs, embeddings, vector stores, multi-agent orchestration, evaluation |
| `ai_shared` | Auth, caching, observability, compliance, cost tracking, governance, security |

### What's New in v1.1.0

- **Multi-Agent Orchestration** — 6 coordination modes: Sequential, Parallel, Debate, Hierarchical, Swarm, Supervisor
- **MessageBus** — Pub/sub system with dead-letter queues and topic-based routing
- **AgentPipelineBuilder** — Fluent API for composing agent pipelines
- **Domain Examples** — Real-world examples: Medical (HIPAA), E-commerce, Real Estate, Loan Processing
- **Expanded Compliance** — Real verification methods for HIPAA, GDPR, SOC2, PCI-DSS
- **247 Tests** — Comprehensive test coverage across all modules (agents, compliance, governance, cost)

---

## Workspace Structure

```
AICoreAndShared/
├── ai_core/                    # Core AI/ML library
│   ├── agents.py               # Multi-agent orchestration: 6 coordination modes, MessageBus, AgentPipelineBuilder
│   ├── chunking.py             # 10 chunking strategies
│   ├── config.py               # LibConfig (env / YAML / Vault / AWS Secrets)
│   ├── deployment.py           # Geo-routing, edge deployment, hybrid cloud
│   ├── embeddings.py           # 8 embedding providers
│   ├── eval.py                 # RAG evaluation (built-in, RAGAS, DeepEval)
│   ├── frameworks.py           # LangChain, LangGraph, CrewAI, AutoGen, MCP adapters
│   ├── llm.py                  # 8 LLM providers (OpenAI, Anthropic, Azure, …)
│   ├── prompts.py              # 15 prompt strategies + registry + dynamic examples
│   ├── rag.py                  # Full RAG pipeline with hooks
│   ├── recovery.py             # Failover, backup, chaos engineering, DR tests
│   ├── reranker.py             # 4 reranker providers
│   ├── schemas.py              # All Pydantic v2 models and enums (CoordinationMode, etc.)
│   └── search.py               # 10 search strategies
│
├── ai_shared/                  # Shared enterprise utilities
│   ├── auth.py                 # JWT, API keys, RBAC
│   ├── cache.py                # Exact, semantic, Redis, multi-layer caching
│   ├── compliance.py           # SOC2/ISO27001/GDPR/HIPAA/FedRAMP/PCI-DSS (real verification)
│   ├── cost.py                 # Cost tracking, optimization, quota management
│   ├── experiments.py          # Feature flags, A/B testing, experiment analytics
│   ├── governance.py           # Data classification, lineage, policies, GDPR
│   ├── logging_utils.py        # Structured JSON logging, log context, decorators
│   ├── memory.py               # 6 memory backends (buffer, summary, vector, Redis, Postgres, entity)
│   ├── models.py               # Model registry, A/B testing, rollback manager
│   ├── observability.py        # Tracing, metrics, exporters (LangSmith, Langfuse, OTEL)
│   ├── plugins.py              # Plugin registry, hooks, lifecycle management
│   ├── resilience.py           # Retry, circuit breaker, rate limiter, timeout
│   ├── security.py             # PII detection, content filtering, input validation
│   └── tokens.py               # Token counting, cost estimation, budget management
│
├── examples/                   # Runnable sample scripts
│   ├── 01_basic_rag.py              # RAG pipeline: ingest → query → stream
│   ├── 02_agent_system.py           # ReAct agent + multi-agent coordination
│   ├── 03_compliance_governance.py  # GDPR, PII, audit, policy enforcement
│   ├── 04_cost_optimization.py      # Cost tracking, quota, token budgets, A/B model testing
│   ├── 05_caching_resilience.py     # Multi-layer cache, circuit breaker, rate limiter
│   ├── 06_full_enterprise_pipeline.py  # All modules integrated end-to-end
│   ├── 07_medical_domain.py         # HIPAA-compliant hierarchical multi-agent (medical records)
│   ├── 08_ecommerce_domain.py       # Parallel + swarm coordination (order intelligence)
│   ├── 09_real_estate_domain.py     # Debate coordination (property valuation)
│   └── 10_loan_processing_domain.py # Supervisor coordination (underwriting pipeline)
│
├── tests/                      # 247 tests — all passing
│   ├── test_core/
│   │   ├── test_agents.py      # 44 tests: ToolRegistry, MessageBus, 6 coordination modes, PipelineBuilder
│   │   ├── test_chunking.py    # Chunking strategies, Chunk.text/index fields
│   │   ├── test_rag.py         # RAG pipeline, cost limits, streaming
│   │   └── test_schemas.py     # Pydantic v2 models, enums, field validation
│   └── test_shared/
│       ├── test_cache.py       # ExactCache, SemanticCache, MultiLayerCache (async)
│       ├── test_compliance.py  # 20 tests: HIPAA, GDPR, SOC2, PCI-DSS verification
│       ├── test_cost.py        # 18 tests: CostTracker, CostOptimizer, QuotaManager
│       ├── test_governance.py  # 28 tests: PolicyEngine, AuditLogger, DataLineageTracker
│       ├── test_security.py    # PII detection, content filtering, input validation
│       └── test_tokens.py      # TokenBudget, TokenCounter, usage tracking
│
├── UI/                         # Frontend documentation app (React + Vite)
│   ├── src/                    # React + TypeScript components and pages
│   │   ├── pages/              # All doc/feature pages including DomainExamplesPage
│   │   └── components/         # Layout, AnimatedPipeline, WorkflowRenderer, UI primitives
│   ├── docs/                   # Architecture and API documentation (Markdown)
│   └── public/                 # Static assets (404.html for SPA routing)
│
├── pyproject.toml              # Package metadata + optional dependency groups
├── requirements.txt            # Pinned development dependencies
├── .env.example                # Environment variable reference
└── Makefile                    # Dev workflow commands
```

---

## Quick Start

### 1. Install

```bash
# Core only
pip install -e ".[core]"

# With OpenAI + Qdrant
pip install -e ".[openai,qdrant,tiktoken]"

# Full install
pip install -e ".[all]"

# Development (includes lint, type-check, test tools)
make install-dev
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run an example

```bash
# Basic RAG pipeline
python examples/01_basic_rag.py

# Multi-agent system
python examples/02_agent_system.py

# Full enterprise pipeline
python examples/06_full_enterprise_pipeline.py

# Domain-specific examples
python examples/07_medical_domain.py       # HIPAA hierarchical agents
python examples/08_ecommerce_domain.py    # Parallel/swarm coordination
python examples/09_real_estate_domain.py  # Debate coordination
python examples/10_loan_processing_domain.py  # Supervisor orchestration
```

---

## Core Concepts

### RAG Pipeline

```python
from ai_core import RAGConfig
from ai_core.rag import RAGPipeline
from ai_core.llm import LLMFactory
from ai_core.embeddings import EmbeddingFactory
from ai_core.vectorstore import VectorStoreFactory
from ai_core.schemas import ChunkingStrategy, SearchStrategy

config = RAGConfig(
    llm_provider="openai",
    llm_model="gpt-4o-mini",
    embedding_provider="openai",
    vector_store_provider="chroma",
    chunking_strategy=ChunkingStrategy.RECURSIVE,
    search_strategy=SearchStrategy.HYBRID,
    top_k=5,
    rerank=True,
)

pipeline = RAGPipeline(config)
response = await pipeline.query("What is quantum entanglement?")
print(response.answer)
```

### Agents

```python
from ai_core.agents import AgentExecutor, tool
from ai_core.schemas import AgentType
from ai_core.llm import LLMFactory

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

llm = LLMFactory.create("openai", "gpt-4o-mini")
agent = AgentExecutor.create(AgentType.REACT, llm=llm, tools=[search_web])
result = await agent.run("What is the latest news about AI?")
```

### Multi-Agent Orchestration

Six coordination modes for complex pipelines:

```python
from ai_core.agents import MultiAgentSystem, AgentPipelineBuilder
from ai_core.schemas import CoordinationMode

# 1. Sequential — agents run one after another
system = MultiAgentSystem(agents=[research, analyst, writer], mode=CoordinationMode.SEQUENTIAL)
result = await system.run("Summarise the Q4 earnings report.")

# 2. Parallel — all agents run concurrently, results merged
system = MultiAgentSystem(agents=[price_agent, inventory_agent, review_agent], mode=CoordinationMode.PARALLEL)

# 3. Debate — agents exchange critique rounds until consensus
system = MultiAgentSystem(agents=[bull_agent, bear_agent], mode=CoordinationMode.DEBATE, rounds=3)

# 4. Hierarchical — supervisor delegates to specialist workers
system = MultiAgentSystem(agents=[supervisor, triage, specialist], mode=CoordinationMode.HIERARCHICAL)

# 5. Swarm — agents collaborate in a shared workspace
system = MultiAgentSystem(agents=[extractor, validator, mapper], mode=CoordinationMode.SWARM)

# 6. Supervisor — one coordinator manages dynamic task routing
system = MultiAgentSystem(agents=[coordinator, underwriter, appraiser], mode=CoordinationMode.SUPERVISOR)

# Fluent pipeline builder
pipeline = (
    AgentPipelineBuilder()
    .add_stage("intake",   intake_agent)
    .add_stage("analyse",  analysis_agent)
    .add_stage("report",   report_agent)
    .with_mode(CoordinationMode.SEQUENTIAL)
    .build()
)
result = await pipeline.run("Process loan application #A-2024-001")
```

### Domain Examples

| Domain | Mode | Compliance | Example |
|---|---|---|---|
| Medical Records | Hierarchical | HIPAA | `examples/07_medical_domain.py` |
| E-commerce Intelligence | Parallel + Swarm | SOC2 | `examples/08_ecommerce_domain.py` |
| Real Estate Valuation | Debate | — | `examples/09_real_estate_domain.py` |
| Loan Underwriting | Supervisor | PCI-DSS | `examples/10_loan_processing_domain.py` |

### Observability

```python
from ai_shared.observability import Tracer, trace, metrics

tracer = Tracer()

@trace("my_function")
async def process(data: str) -> str:
    metrics.increment("requests_total")
    return data.upper()
```

### Security

```python
from ai_shared.security import PIIDetector, ContentFilter, InputValidator

detector = PIIDetector()
result = detector.detect("Call me at 555-1234 or john@example.com")
print(result)  # ['phone', 'email']

safe_text = detector.redact("SSN: 123-45-6789")
print(safe_text)  # "SSN: [REDACTED]"
```

---

## Optional Dependency Groups

| Group | Contents |
|---|---|
| `openai` | openai SDK |
| `anthropic` | anthropic SDK |
| `azure` | openai + azure-identity |
| `bedrock` | boto3 |
| `vertex` | google-generativeai |
| `groq` | groq SDK |
| `ollama` | ollama SDK |
| `qdrant` | qdrant-client |
| `pinecone` | pinecone-client |
| `chroma` | chromadb |
| `weaviate` | weaviate-client |
| `milvus` | pymilvus |
| `pgvector` | asyncpg |
| `redis` | redis |
| `cohere` | cohere + sentence-transformers |
| `tiktoken` | tiktoken |
| `jwt` | PyJWT |
| `langsmith` | langsmith |
| `langfuse` | langfuse |
| `otel` | opentelemetry |
| `langchain` | langchain + langgraph |
| `crewai` | crewai |
| `autogen` | pyautogen |
| `ragas` | ragas |
| `deepeval` | deepeval |
| `all` | everything above |

---

## Testing

```bash
make test          # run all 247 tests with coverage
make test-fast     # pytest -x (stop on first failure)
pytest tests/test_core/test_agents.py -v      # 44 agent tests (6 coordination modes)
pytest tests/test_shared/test_compliance.py   # HIPAA/GDPR/SOC2/PCI-DSS
pytest tests/test_shared/test_governance.py   # PolicyEngine, AuditLogger, DataLineageTracker
pytest tests/test_shared/test_cost.py         # CostTracker, CostOptimizer, QuotaManager
```

| Module | Tests | Status |
|---|---|---|
| `test_agents.py` | 44 | ✅ passing |
| `test_schemas.py` | 28 | ✅ passing |
| `test_chunking.py` | 18 | ✅ passing |
| `test_rag.py` | 22 | ✅ passing |
| `test_cache.py` | 25 | ✅ passing |
| `test_compliance.py` | 20 | ✅ passing |
| `test_cost.py` | 18 | ✅ passing |
| `test_governance.py` | 28 | ✅ passing |
| `test_security.py` | 30 | ✅ passing |
| `test_tokens.py` | 14 | ✅ passing |
| **Total** | **247** | **✅ all passing** |

---

## Development

```bash
make lint        # ruff check + fix
make typecheck   # mypy --strict
make test        # pytest with coverage
make test-fast   # pytest -x (stop on first failure)
make fmt         # ruff format
make clean       # remove build artifacts
```

---

## Architecture Documentation

> **Browse online:** https://venkateshTechmates.github.io/AICoreAndShared/

See [`UI/docs/`](UI/docs/) for:
- [01 — Core Library](UI/docs/01-core-library.md)
- [02 — Shared Library](UI/docs/02-shared-library.md)
- [03 — Architecture & Workflows](UI/docs/03-architecture-workflows.md)
- [04 — Trends & Design Patterns](UI/docs/04-trends-design-patterns.md)
- [05 — Enterprise Operations](UI/docs/05-enterprise-operations.md)

### Run the documentation app locally

```bash
cd UI && npm install && npm run dev
```
