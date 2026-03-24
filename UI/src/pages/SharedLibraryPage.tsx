import { SectionHeader, CodeBlock, Accordion } from '../components/ui';

const sharedModules = [
  { title: 'Configuration Management', module: 'ai_core.config', desc: 'Hierarchical config from env, YAML, Vault, and AWS Secrets with override precedence.', code: 'from ai_core.config import LibConfig\n\nconfig = LibConfig.from_env()           # .env\nconfig = LibConfig.from_yaml(\"ai.yml\")  # YAML\nconfig = LibConfig.from_vault(\"kv/ai\")  # Vault\n\n# Override precedence:\n# defaults > yaml > .env > env vars > runtime' },
  { title: 'LLM Provider Abstraction', module: 'ai_core.llm', desc: 'Unified interface for 8+ LLM providers with retry, rate limiting, fallback, streaming, and structured output.', code: 'from ai_core.llm import LLMFactory\n\nllm = LLMFactory.create(\n    provider=\"openai\", model=\"gpt-4o\",\n    config=LLMConfig(max_retries=3, fallback_model=\"gpt-4-turbo\")\n)\n\nresponse = await llm.generate(\"Summarize...\")\nprint(response.text, response.cost, response.latency_ms)\n\nasync for chunk in llm.stream(\"Explain...\"):\n    print(chunk.text, end=\"\")' },
  { title: 'Embedding Abstraction', module: 'ai_core.embeddings', desc: 'Multi-provider embedding with batch support, normalization, and dimension control.', code: 'from ai_core.embeddings import EmbeddingFactory\n\nembedder = EmbeddingFactory.create(\n    provider=\"openai\",\n    model=\"text-embedding-3-large\",\n    config=EmbeddingConfig(dimensions=3072, batch_size=512)\n)\n\nvectors = await embedder.embed_batch(texts, show_progress=True)' },
  { title: 'Memory & State', module: 'ai_core.memory', desc: '6 memory types: Buffer, Summary, Vector, Redis, Postgres, Entity.', code: 'from ai_core.memory import VectorMemory, RedisMemory\n\nmemory = VectorMemory(store=vector_store, top_k=5)\nmemory = RedisMemory(url=\"redis://localhost:6379\", ttl=3600)' },
  { title: 'Observability & Tracing', module: 'ai_core.observability', desc: 'Integrates with LangSmith, Langfuse, Arize, OpenTelemetry, Prometheus.', code: 'from ai_core.observability import Tracer\n\n@Tracer.trace(name=\"rag_pipeline\", track_tokens=True, track_cost=True)\nasync def run_pipeline(query: str):\n    ...\n\n# Prometheus metrics:\n# ai_core_llm_requests_total{provider, model}\n# ai_core_llm_latency_seconds{quantile}\n# ai_core_llm_cost_dollars{provider}' },
  { title: 'Token Budget', module: 'ai_core.tokens', desc: 'Token counting, budget enforcement, and context fitting strategies.', code: 'from ai_core.tokens import TokenBudget\n\nbudget = TokenBudget(\n    model=\"gpt-4o\",\n    max_input_tokens=100_000,\n    max_output_tokens=4_096,\n    context_strategy=\"truncate_middle\",\n)\n\nsafe_prompt = budget.fit(prompt, retrieved_context)' },
  { title: 'Caching', module: 'ai_core.cache', desc: 'Semantic cache, exact cache, and multi-layer cache for LLM response deduplication.', code: 'from ai_core.cache import SemanticCache\n\ncache = SemanticCache(\n    store=\"redis\",\n    embedding_model=\"text-embedding-3-small\",\n    similarity_threshold=0.97,\n    ttl_seconds=3600,\n)\n\nresult = await cache.get(query)\nif result is None:\n    result = await rag.query(query)\n    await cache.set(query, result)' },
  { title: 'Security', module: 'ai_core.security', desc: 'PII detection (Presidio), content filtering, and input validation.', code: 'from ai_core.security import PIIDetector, ContentFilter\n\ndetector = PIIDetector(engine=\"presidio\")\nredacted = detector.redact(\"John Doe email is john@example.com\")\n# -> \"[PERSON] email is [EMAIL]\"\n\nfilter = ContentFilter(block_categories=[\"violence\", \"hate_speech\"])\nis_safe = await filter.check(user_input)' },
  { title: 'Auth & RBAC', module: 'ai_core.auth', desc: 'API key management, RBAC with role-based permissions, JWT validation.', code: 'from ai_core.auth import RBAC\n\nrbac = RBAC(roles={\n    \"admin\": [\"*\"],\n    \"data_scientist\": [\"rag.query\", \"rag.ingest\", \"eval.*\"],\n    \"viewer\": [\"rag.query\"],\n})\n\nif rbac.has_permission(user, \"rag.ingest\"):\n    await rag.ingest(documents)' },
  { title: 'Resilience', module: 'ai_core.resilience', desc: 'Retry with exponential backoff, circuit breaker, and rate limiter patterns.', code: 'from ai_core.resilience import RetryPolicy, CircuitBreaker\n\n@RetryPolicy(max_retries=3, backoff=\"exponential\")\nasync def call_llm(prompt):\n    return await llm.generate(prompt)\n\nbreaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)\nasync with breaker:\n    result = await external_api.call()' },
  { title: 'Plugin System', module: 'ai_core.plugins', desc: 'Register custom vector stores, LLMs, embeddings, chunkers, and search strategies.', code: 'from ai_core.plugins import register_plugin\n\n@register_plugin(\"vectorstore\")\nclass MyCustomStore(VectorStoreBase):\n    provider = \"my_db\"\n    async def upsert(self, docs): ...\n    async def search(self, query): ...' },
  { title: 'Logging', module: 'ai_core.logging', desc: 'Structured JSON logging with rotation, retention, and module-scoped loggers.', code: 'from ai_core.logging import configure_logging, get_logger\n\nconfigure_logging(level=\"INFO\", format=\"json\", rotation=\"100MB\")\n\nlogger = get_logger(\"rag.pipeline\")\nlogger.info(\"Pipeline started\", query=query, namespace=ns)' },
];

const SharedLibraryPage = () => (
  <div className="space-y-16">
    <SectionHeader badge="Shared Components" title="Shared Library Utilities & Infrastructure" subtitle="Cross-cutting utilities consumed by all core modules: config, LLM abstraction, memory, caching, security, and more." />
    <div className="space-y-4">
      {sharedModules.map((m, i) => (
        <Accordion key={i} title={(i + 1) + '. ' + m.title} defaultOpen={i === 0}>
          <div className="space-y-4">
            <span className="text-xs font-mono bg-zinc-100 text-zinc-500 px-2 py-1 rounded">{m.module}</span>
            <p className="text-sm text-zinc-500">{m.desc}</p>
            <CodeBlock code={m.code} />
          </div>
        </Accordion>
      ))}
    </div>
  </div>
);

export default SharedLibraryPage;
