# AI Enterprise Toolkit

**Version:** 1.1.0 | **Python:** 3.11+ | **License:** MIT

A production-ready, enterprise-grade AI library split into two packages:

| Package | Purpose |
|---|---|
| `ai_core` | RAG pipelines, LLMs, embeddings, vector stores, agents, evaluation |
| `ai_shared` | Auth, caching, observability, compliance, cost tracking, governance |

---

## Workspace Structure

```
AIMainCoreAndShared/
├── ai_core/                    # Core AI/ML library
│   ├── agents.py               # ReAct, PlanExecute, Reflexion, FunctionCall agents
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
│   ├── schemas.py              # All Pydantic v2 models and enums
│   └── search.py               # 10 search strategies
│
├── ai_shared/                  # Shared enterprise utilities
│   ├── auth.py                 # JWT, API keys, RBAC
│   ├── cache.py                # Exact, semantic, Redis, multi-layer caching
│   ├── compliance.py           # SOC2/ISO27001/GDPR/HIPAA/FedRAMP/PCI-DSS
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
│   ├── 01_basic_rag.py         # RAG pipeline: ingest → query → stream
│   ├── 02_agent_system.py      # ReAct agent + multi-agent coordination
│   ├── 03_compliance_governance.py  # GDPR, PII, audit, policy enforcement
│   ├── 04_cost_optimization.py # Cost tracking, quota, token budgets, A/B model testing
│   ├── 05_caching_resilience.py     # Multi-layer cache, circuit breaker, rate limiter
│   └── 06_full_enterprise_pipeline.py  # All modules integrated end-to-end
│
├── tests/                      # Test suite
│   ├── test_core/
│   │   ├── test_schemas.py
│   │   ├── test_chunking.py
│   │   └── test_rag.py
│   └── test_shared/
│       ├── test_cache.py
│       ├── test_security.py
│       └── test_tokens.py
│
├── AICoreAndShared/            # Frontend documentation app (Node.js / Vite)
│   ├── src/                    # React + TypeScript components
│   └── docs/                   # Architecture and API documentation
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

See [`AICoreAndShared/docs/`](AICoreAndShared/docs/) for:
- [01 — Core Library](AICoreAndShared/docs/01-core-library.md)
- [02 — Shared Library](AICoreAndShared/docs/02-shared-library.md)
- [03 — Architecture & Workflows](AICoreAndShared/docs/03-architecture-workflows.md)
- [04 — Trends & Design Patterns](AICoreAndShared/docs/04-trends-design-patterns.md)
- [05 — Enterprise Operations](AICoreAndShared/docs/05-enterprise-operations.md)

Frontend documentation app: `cd AICoreAndShared && npm install && npm run dev`
